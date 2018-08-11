"""Classes following the PICMI standard
"""
import re
import PICMI_Base
import numpy as np
from .warp import *
from .init_tools.plasma_initialization import PlasmaInjector
import warp

codename = 'warp'
PICMI_Base.register_codename(codename)

c = warp.clight
ep0 = warp.eps0
mu0 = warp.mu0
q_e = warp.echarge
m_e = warp.Electron.mass
m_p = warp.Proton.mass

# --- Always assume that relativity should be turned on.
warp.top.lrelativ = warp.true

# --- Species name dictionary.
# --- This maps the PICMI type (a string) to the Warp species types
# --- This will go in a separate file, since it will be big.
species_type_dict = {'electron':warp.Electron,
                     'positron':warp.Positron,
                     'proton':warp.Proton}
# --- Add all of the elements to the dictionary
for name,d in warp.periodic_table.items():
    symbol = d['Symbol']
    m = re.search('[0-9]', symbol)
    if m is not None:
        symbol = '#' + m.group() + symbol
    species_type_dict[symbol] = getattr(warp, name)


# --- Code to handle the instance of Boosted_Frame if needed
_boosted_frame = None
def set_boosted_frame(gamma_boost):
    global _boosted_frame
    assert _boosted_frame is None, Exception('There can be only one boosted frame')
    from .run_modes.boosted_frame import Boosted_Frame
    _boosted_frame = Boosted_Frame(gamma_boost, direction=1.)
def get_boosted_frame():
    return _boosted_frame


class Species(PICMI_Base.PICMI_Species):
    def init(self, kw):

        # --- When using the PICMI standard, always make the particles
        # --- have variable weights. This will greatly simplify the
        # --- handling of particle initialization. The species weight
        # --- will be set to 1, and the variable weight will hold
        # --- the actual weight.

        wtype = species_type_dict.get(self.particle_type, None)
        self.wspecies = warp.Species(type = wtype,
                                     name = self.name,
                                     charge = self.charge,
                                     charge_state = self.charge_state,
                                     mass = self.mass,
                                     lvariableweights = True,
                                     weight = 1.)

    def initialize_inputs(self, layout):

        if self.particle_shape is not None:
            if isinstance(self.particle_shape, str):
                interpolation_order = {'NGP':0, 'linear':1, 'quadratic':2, 'cubic':3}[self.particle_shape]
            else:
                interpolation_order = self.particle_shape
            self.wspecies.depos_order = interpolation_order

        if self.initial_distribution is not None:
            self.layout = layout
            installparticleloader(self.particle_loader)

    def particle_loader(self):
        self.initial_distribution.loaddistribution(self.wspecies, self.layout)


PICMI_Base.PICMI_MultiSpecies.Species_class = Species
class MultiSpecies(PICMI_Base.PICMI_MultiSpecies):
    pass


class GaussianBunchDistribution(PICMI_Base.PICMI_GaussianBunchDistribution):
    def loaddistribution(self, species, layout):
        assert isinstance(layout, PseudoRandomLayout), Exception('Warp only supports PseudoRandomLayout with GaussianBunchDistribution')
        assert layout.n_macroparticles is not None, Exception('Warp only support n_macroparticles with PseudoRandomLayout with GaussianBunchDistribution')
        np = layout.n_macroparticles
        deltax = self.rms_bunch_size[0]
        deltay = self.rms_bunch_size[1]
        deltaz = self.rms_bunch_size[2]
        vthx = self.rms_velocity[0]
        vthy = self.rms_velocity[1]
        vthz = self.rms_velocity[2]
        xmean = self.centroid_position[0]
        ymean = self.centroid_position[1]
        zmean = self.centroid_position[2]
        vxmean = self.centroid_velocity[0]
        vymean = self.centroid_velocity[1]
        vzmean = self.centroid_velocity[2]
        vxdiv = self.velocity_divergence[0]
        vydiv = self.velocity_divergence[1]
        vzdiv = self.velocity_divergence[2]
        w = self.n_physical_particles/np
        species.add_gaussian_dist(np, deltax, deltay, deltaz, vthx, vthy, vthz,
                                  xmean, ymean, zmean, vxmean, vymean, vzmean, vxdiv, vydiv, vzdiv,
                                  zdist='random', rdist='linear', fourfold=False, lmomentum=True, w=w)

        # --- The parameters describing the bunch are in the lab frame. The particles generated
        # --- need to be transformed in to the boosted frame.
        boosted_frame = get_boosted_frame()
        if boosted_frame is not None:
            boosted_frame.boost(species, l_inject_plane=False, lallindomain=False)


class UniformDistribution(PICMI_Base.PICMI_UniformDistribution):
    def loaddistribution(self, species, layout):
        xmin = self.lower_bound[0]
        ymin = self.lower_bound[1]
        zmin = self.lower_bound[2]
        xmax = self.upper_bound[0]
        ymax = self.upper_bound[1]
        zmax = self.upper_bound[2]
        ux_th = self.rms_velocity[0]
        uy_th = self.rms_velocity[1]
        uz_th = self.rms_velocity[2]
        ux_m = self.directed_velocity[0]
        uy_m = self.directed_velocity[1]
        uz_m = self.directed_velocity[2]

        # --- The inputs are in the lab frame and need to be transformed into the boosted frame.
        boosted_frame = get_boosted_frame()
        if boosted_frame is not None:
            boost = BoostConverter(boosted_frame.gammaframe)
            if zmin is not None:
                zmin, = boost.static_length([zmin])
            if zmax is not None:
                zmax, = boost.static_length([zmax])
            if uz_th is not None:
                uz_th, = boost.longitudinal_momentum([uz_th])
            if uz_m is not None:
                uz_m, = boost.longitudinal_momentum([uz_m])

        if isinstance(layout, GriddedLayout):
            # --- Note that layout.grid is ignored
            p_nx = layout.n_macroparticle_per_cell[0]
            p_ny = layout.n_macroparticle_per_cell[1]
            p_nz = layout.n_macroparticle_per_cell[2]

            npreal_per_cell = self.density*w3d.dx*w3d.dy*w3d.dz
            w = npreal_per_cell/(p_nx*p_ny*p_nz)
            if boosted_frame is not None:
                w, = boost.static_density([w])
            def dens_func(x, y, z, w=w):
                return w

            if top.vbeamfrm > 0:
                injection_direction = +1
            else:
                injection_direction = -1
            plasmainjector = PlasmaInjector(elec=species, ions=None, w3d=w3d, top=top, dim='3d',
                                            p_nx=p_nx, p_ny=p_ny, p_nz=p_nz,
                                            p_xmin=xmin, p_ymin=xmin, p_zmin=zmin,
                                            p_xmax=xmax, p_ymax=ymax, p_zmax=zmax,
                                            dens_func=dens_func,
                                            ux_m=ux_m, uy_m=uy_m, uz_m=uz_m,
                                            ux_th=ux_th, uy_th=uy_th, uz_th=uz_th,
                                            injection_direction=injection_direction)
            if self.fill_in:
                installuserinjection(plasmainjector.continuous_injection)

        elif isinstance(layout, PseudoRandomLayout):
            assert not self.fill_in, Exception('Warp does not support fill_in with PseudoRandomLayout')
            if layout.n_macroparticles_per_cell is not None:
                np = layout.n_macroparticles_per_cell*w3d.nx*w3d.ny*w3d.nz
            elif layout.n_macroparticles is not None:
                np = layout.n_macroparticles
            npreal = self.density*(xmax - xmin)*(ymax - ymin)*(zmax - zmin)
            w = np.full(np, npreal/np)
            if boosted_frame is not None:
                w, = boost.static_density([w])
            species.add_uniform_box(np=np, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, zmin=zmin, zmax=zmax,
                                    vthx=ux_th, vthy=uy_th, vthz=uz_th,
                                    vxmean=ux_m, vymean=uy_m, vzmean=uz_m,
                                    lmomentum=1, spacing='random',
                                    lallindomain=warp.true,
                                    w=w)


class AnalyticDistribution(PICMI_Base.PICMI_AnalyticDistribution):
    def loaddistribution(self, species, layout):
        xmin = self.lower_bound[0]
        ymin = self.lower_bound[1]
        zmin = self.lower_bound[2]
        xmax = self.upper_bound[0]
        ymax = self.upper_bound[1]
        zmax = self.upper_bound[2]
        ux_th = self.rms_velocity[0]
        uy_th = self.rms_velocity[1]
        uz_th = self.rms_velocity[2]
        ux_m = self.directed_velocity[0]
        uy_m = self.directed_velocity[1]
        uz_m = self.directed_velocity[2]

        if uz_m is not None:
          gg = np.sqrt(1. + (uz_m/c)**2)
          betaz_lab = uz_m/gg
        else:
          betaz_lab = 0.

        # --- The inputs are in the lab frame and need to be transformed into the boosted frame.
        boosted_frame = get_boosted_frame()
        if boosted_frame is not None:
            boost = BoostConverter(boosted_frame.gammaframe)
            if zmin is not None:
                zmin, = boost.static_length([zmin])
            if zmax is not None:
                zmax, = boost.static_length([zmax])
            if uz_th is not None:
                uz_th, = boost.longitudinal_momentum([uz_th])
            if uz_m is not None:
                uz_m, = boost.longitudinal_momentum([uz_m])

        if isinstance(layout, GriddedLayout):
            # --- Note that layout.grid is ignored
            p_nx = layout.n_macroparticle_per_cell[0]
            p_ny = layout.n_macroparticle_per_cell[1]
            p_nz = layout.n_macroparticle_per_cell[2]

            if isinstance(self.density_expression, str):
                cell_volume_per_particle = w3d.dx*w3d.dy*w3d.dz/(p_nx*p_ny*p_nz)
                def dens_func(x, y, z, density = self.density_expression,
                                       cell_volume_per_particle = cell_volume_per_particle,
                                       boosted_frame = boosted_frame,
                                       betaz_lab = betaz_lab):
                    if boosted_frame is not None:
                        z = boosted_frame.gammaframe*(z*(1 - boosted_frame.betaframe*betaz_lab) - c*top.time*(betaz_lab-boosted_frame.betaframe))

                    # --- Include globals so that numpy is available
                    self.user_defined_kw['__builtins__'] = {}
                    self.user_defined_kw['x'] = x
                    self.user_defined_kw['y'] = y
                    self.user_defined_kw['z'] = z
                    d = eval(density, self.user_defined_kw)

                    if boosted_frame is not None:
                        d, = boost.static_density([d])

                    return d*cell_volume_per_particle
            else:
                npreal_per_cell = self.density_expression*w3d.dx*w3d.dy*w3d.dz
                w = npreal_per_cell/(p_nx*p_ny*p_nz)
                def dens_func(x, y, z, w=w):
                    return w

            if top.vbeamfrm > 0:
                injection_direction = +1
            else:
                injection_direction = -1
            plasmainjector = PlasmaInjector(elec=species, ions=None, w3d=w3d, top=top, dim='3d',
                                            p_nx=p_nx, p_ny=p_ny, p_nz=p_nz,
                                            p_xmin=xmin, p_ymin=xmax, p_zmin=zmin,
                                            p_xmax=xmax, p_ymax=ymax, p_zmax=zmax,
                                            dens_func=dens_func,
                                            ux_m=ux_m, uy_m=uy_m, uz_m=uz_m,
                                            ux_th=ux_th, uy_th=uy_th, uz_th=uz_th,
                                            injection_direction=injection_direction)
            if self.fill_in:
                installuserinjection(plasmainjector.continuous_injection)

        elif isinstance(layout, PseudoRandomLayout):
            assert not self.fill_in, Exception('Warp does not support fill_in with PseudoRandomLayout')
            assert not isinstance(self.density_expression, str), Exception('Warp does not support PseudoRandomLayout with nonuniform distribution')
            if layout.n_macroparticles_per_cell is not None:
                nn = layout.n_macroparticles_per_cell*w3d.nx*w3d.ny*w3d.nz
            elif layout.n_macroparticles is not None:
                nn = layout.n_macroparticles
            npreal = self.density_expression*(xmax - xmin)*(ymax - ymin)*(zmax - zmin)
            w = np.full(nn, npreal/nn)
            if boosted_frame is not None:
                w, = boost.static_density([w])
            species.add_uniform_box(np=nn, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, zmin=zmin, zmax=zmax,
                                    vthx=ux_th, vthy=uy_th, vthz=uz_th,
                                    vxmean=ux_m, vymean=uy_m, vzmean=uz_m,
                                    lmomentum=1, spacing='random',
                                    lallindomain=warp.true,
                                    w=w)


class ParticleList(PICMI_Base.PICMI_ParticleList):
    def loaddistribution(self, species, layout):
        species.addparticles(x=self.x, y=self.y, z=self.z, ux=self.ux, uy=self.uy, uz=self.uz,
                             vx=None, vy=None, vz=None)


class ParticleDistributionPlanarInjector(PICMI_Base.PICMI_ParticleDistributionPlanarInjector):
    pass


class GriddedLayout(PICMI_Base.PICMI_GriddedLayout):
    pass


class PseudoRandomLayout(PICMI_Base.PICMI_PseudoRandomLayout):
    pass


class BinomialSmoother(PICMI_Base.PICMI_BinomialSmoother):
    def initialize_inputs(self, ndims):
        # --- Setup the list of smoothing parameters
        n_pass = self.n_pass
        alpha = self.alpha
        stride = self.stride
        if n_pass is None:
            n_pass = 3*[[1]]
        if alpha is None:
            alpha = 3*[[0.5]]
        if stride is None:
            stride = 3*[[1]]

        if ndims == 1:
            for i in range(len(n_pass[0])):
                n_pass[0][i] = 0
        if ndims < 3:
            for i in range(len(n_pass[1])):
                n_pass[1][i] = 0

        if self.compensation is not None:
            n_pass = list(n_pass)
            alpha = list(alpha)
            stride = list(stride)
            for i in range(len(n_pass)):
                n_pass[i] = list(n_pass[i])
                alpha[i] = list(alpha[i])
                stride[i] = list(stride[i])
                for j in range(len(n_pass[i])):
                    if self.compensation[i]:
                        n_pass[i].append(1)
                    else:
                        n_pass[i].append(0)
                    alpha[i].append(n_pass[i][j]*(1. - alpha[i][0]) + 1.)
                    stride[i].append(stride[i][j])

        self.n_pass = np.array(n_pass)
        self.alpha = np.array(alpha)
        self.stride = np.array(stride)


class CylindricalGrid(PICMI_Base.PICMI_CylindricalGrid):
    def init(self, kw):
        raise Exception('WarpX does not support CylindricalGrid yet')


class Cartesian2DGrid(PICMI_Base.PICMI_Cartesian2DGrid):
    def init(self, kw):
        raise Exception('WarpX does not support Cartesian2DGrid yet')


class Cartesian3DGrid(PICMI_Base.PICMI_Cartesian3DGrid):
    def initialize_inputs(self):
        w3d.nx = self.nx
        w3d.ny = self.ny
        w3d.nz = self.nz
        w3d.xmmin = self.xmin
        w3d.xmmax = self.xmax
        w3d.ymmin = self.ymin
        w3d.ymmax = self.ymax
        w3d.zmmin = self.zmin
        w3d.zmmax = self.zmax

        boosted_frame = get_boosted_frame()
        if boosted_frame is not None:
            boost = BoostConverter(boosted_frame.gammaframe)
            w3d.zmmin, w3d.zmmax = boost.copropag_length([w3d.zmmin, w3d.zmmax])


        bc_dict = {'dirichlet':warp.dirichlet,
                        'neumann':warp.neumann,
                        'periodic':warp.periodic,
                        'open':warp.openbc}
        self.bounds = [bc_dict[self.lower_boundary_conditions[0]], bc_dict[self.upper_boundary_conditions[0]],
                       bc_dict[self.lower_boundary_conditions[1]], bc_dict[self.upper_boundary_conditions[1]],
                       bc_dict[self.lower_boundary_conditions[2]], bc_dict[self.upper_boundary_conditions[2]]]
        w3d.boundxy = self.bounds[1]
        w3d.bound0 = self.bounds[4]
        w3d.boundnz = self.bounds[5]
        top.pboundxy = self.bounds[1]
        top.pbound0 = self.bounds[4]
        top.pboundnz = self.bounds[5]
        if top.pboundxy == warp.openbc: top.pboundxy = warp.absorb
        if top.pbound0 == warp.openbc: top.pbound0 = warp.absorb
        if top.pboundnz == warp.openbc: top.pboundnz = warp.absorb

        if self.moving_window_velocity is not None:
            top.vbeam = top.vbeamfrm = self.moving_window_velocity[2]
            top.lgridqnt = true


class ElectromagneticSolver(PICMI_Base.PICMI_ElectromagneticSolver):
    def init(self, kw):

        self.l_getrho = kw.pop('warp_l_getrho', false)
        self.l_correct_num_Cherenkov = kw.pop('warp_l_correct_num_Cherenkov', False)
        self.l_setcowancoefs = kw.pop('warp_l_setcowancoefs', True)
        self.type_rz_depose = kw.pop('warp_type_rz_depose', 0)
        self.laser_depos_order = kw.pop('warp_laser_depos_order', None)

    def initialize_inputs(self):

        self.grid.initialize_inputs()

        stencil = {'Yee':0, 'CKC':1}[self.method]

        circ_m = 0
        if isinstance(self.grid, CylindricalGrid):
            circ_m = self.grid.n_azimuthal_modes

        npass_smooth = EM3D.__flaginputs__['npass_smooth']
        alpha_smooth = EM3D.__flaginputs__['alpha_smooth']
        stride_smooth = EM3D.__flaginputs__['stride_smooth']
        if self.field_smoother is not None:
            self.field_smoother.initialize_inputs(self.grid.number_of_dimensions)
            npass_smooth = self.field_smoother.n_pass
            alpha_smooth = self.field_smoother.alpha
            stride_smooth = self.field_smoother.stride

        if self.laser_depos_order is None:
            self.laser_depos_order = [EM3D.__flaginputs__['laser_depos_order_x'],
                                      EM3D.__flaginputs__['laser_depos_order_y'],
                                      EM3D.__flaginputs__['laser_depos_order_z']]

        self.solver = EM3D(stencil = stencil,
                           l_getrho = self.l_getrho,
                           l_correct_num_Cherenkov = self.l_correct_num_Cherenkov,
                           l_setcowancoefs = self.l_setcowancoefs,
                           type_rz_depose = self.type_rz_depose,
                           l_2dxz = (self.grid.number_of_dimensions == 2),
                           l_2drz = isinstance(self.grid, CylindricalGrid),
                           circ_m = circ_m,
                           npass_smooth = npass_smooth,
                           alpha_smooth = alpha_smooth,
                           stride_smooth = stride_smooth,
                           laser_depos_order_x = self.laser_depos_order[0],
                           laser_depos_order_y = self.laser_depos_order[1],
                           laser_depos_order_z = self.laser_depos_order[2],
                           )

        registersolver(self.solver)


class Electrostatic_solver(PICMI_Base.PICMI_Electrostatic_solver):
    def initialize_inputs(self):
        self.solver = MultiGrid3d()
        registersolver(self.solver)


class GaussianLaser(PICMI_Base.PICMI_GaussianLaser):
    def initialize_inputs(self, solver, antenna, gamma_boost):
        from .init_tools import add_laser
        dim = '3d'
        antenna_z0 = antenna.position[2]
        add_laser(solver.solver, dim, self.a0, self.waist, self.duration*warp.clight,
                  self.centroid_position[2], self.focal_position[2],
                  lambda0=self.wavelength, theta_pol=self.polarization_angle, source_z=antenna_z0,
                  zeta=0., beta=0., phi2=0., gamma_boost=gamma_boost, laser_file=None, laser_file_energy=None)


class LaserAntenna(PICMI_Base.PICMI_LaserAntenna):
    pass


class Simulation(PICMI_Base.PICMI_Simulation):
    def init(self, kw):
        if self.verbose is not None:
            top.verbosity = self.verbose + 1

        if not hasattr(setup, 'pname'):
            # --- Setup the graphics if needed.
            setup()

        self.inputs_initialized = False

    def initilize_inputs(self):
        if self.inputs_initialized:
            return

        self.inputs_initialized = True

        if self.gamma_boost is not None:
            set_boosted_frame(self.gamma_boost)

        for i in range(len(self.species)):
            if self.species[i].particle_shape is None:
                self.species[i].particle_shape = self.particle_shape
            self.species[i].initialize_inputs(self.layouts[i])

        self.solver.initialize_inputs()

        package('w3d')
        generate()

        for i in range(len(self.lasers)):
            self.lasers[i].initialize_inputs(self.solver, self.laser_injection_methods[i], self.gamma_boost)

    def step(self, nsteps=1):
        self.initilize_inputs()
        step(nsteps)

    def write_input_file(self, file_name='inputs'):
        self.initilize_inputs()
        pass


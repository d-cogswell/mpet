"""This module handles properties associated with the active materials."""
import numpy as np

import mpet.geometry as geo

import types


class Dfuncs():
    """This class returns the filling-fraction dependent variation of
    the transport coefficient, D(y), such that
    Flux = -D_ref*D(y)*grad(y) for solid solution transport or
    Flux = -D_ref*D(y)*grad(mu) for thermo-based transport
    where y here is the filling fraction, D_ref has dimensions of
    length^2/time, D(y) is dimensionless, and mu, the chemical
    potential, has been scaled to the thermal energy, k*Tref. For more
    details on the two forms, see muRfuncs which defines both solid
    solution (_ss) and materials based on simpler thermodynamic models.
    """

    def __init__(self, Dfunc):
        Dopts = {}
        Dopts['lattice'] = self.lattice
        Dopts['constant'] = self.constant
        self.Dfunc = Dopts[Dfunc]

    def constant(self, y):
        return 1.

    def lattice(self, y):
        return y*(1-y)


class muRfuncs():
    """ This class defines functions which describe the chemical
    potential of active materials.
    Each function describes a particular material. The
    chemical potential is directly related to the open circuit voltage
    (OCV) for solid solution materials.
    In each function, muR_ref is the offset (non-dimensional) chemical
    potential by which the returned value will be shifted (for
    numerical convenience).
    Each material function returns:
        muR -- chemical potential
        actR -- activity (if applicable, else None)
    """

    def __init__(self, T, ndD=None, **kwargs):
        """ ndD can be the full dictionary of nondimensional
        parameters for the electrode particles, as made for the
        simulations. Otherwise, parameters can be passed directly in
        as keyword arguments and must contain all of the needed
        parameters for the material of interest.
        E.g.
        For a regular solution material:
            muRfuncs(T, ndD)
        or
            muRfuncs(T, muRfunc="LiFePO4", Omga=3.4)
        For solid solution function based on fit OCV:
            muRfuncs(T, ndD)
        or
            muRfuncs(T, muRfunc="LiMn2O4_ss")
        """
        if ndD is None:
            ndD = kwargs
        self.ndD = ndD
        self.T = T  # nondimensional
        k = 1.381e-23
        Tabs = 298
        e = 1.602e-19
        # eokT and kToe are the reference values for scalings
        self.eokT = e/(k*Tabs)
        self.kToe = (k*Tabs)/e

        # Convert "muRfunc" to a callable function

        # Import module  which contains the function we seek, the path can be
        # adjusted later on to allow for "local" material to be used
        # we need to call __import__ because the module import is dependent
        # on a variable name
        # the following line can be interpreted as
        #   muRmodule = from mpet.electrode.materials.[var] import [var]
        muRmodule = __import__('mpet.electrode.materials.' + ndD["muRfunc"],
                               globals(), locals(), [ndD["muRfunc"]], 0)

        # Extract the function from the module
        muRfunc = getattr(muRmodule,ndD["muRfunc"])

        # Append the function to the instance, we also have to make sure the
        # function knows what 'self' is with the types.MethodType function
        self.muRfunc = types.MethodType(muRfunc, self)

    def get_muR_from_OCV(self, OCV, muR_ref):
        return -self.eokT*OCV + muR_ref

    ######
    # Functions based on thermodynamic models
    ######

    def ideal_sln(self, y, ISfuncs=None):
        """ Helper function: Should not be called directly from
        simulation. Call a specific material instead. """
        T = self.T
        if ISfuncs is not None:
            # Input must be a vector when using ISfuncs
            muR = T*np.array([ISfuncs[i]() for i in range(len(y))])
        else:
            muR = T*np.log(y/(1-y))
        return muR

    def reg_sln(self, y, Omga, ISfuncs=None):
        """ Helper function """
        muR_IS = self.ideal_sln(y, ISfuncs=ISfuncs)
        enthalpyTerm = Omga*(1-2*y)
        muR = muR_IS + enthalpyTerm
        return muR

    def graphite_2param_homog(self, y, Omga, Omgb, Omgc, EvdW, ISfuncs=None):
        """ Helper function """
        y1, y2 = y
        ISfuncs1, ISfuncs2 = ISfuncs
        muR1 = self.reg_sln(y1, Omga, ISfuncs1)
        muR2 = self.reg_sln(y2, Omga, ISfuncs2)
        muR1 += Omgb*y2 + Omgc*y2*(1-y2)*(1-2*y1)
        muR2 += Omgb*y1 + Omgc*y1*(1-y1)*(1-2*y2)
        muR1 += EvdW * (30 * y1**2 * (1-y1)**2)
        muR2 += EvdW * (30 * y2**2 * (1-y2)**2)
        return (muR1, muR2)

    def graphite_1param_homog(self, y, Omga, Omgb, ISfuncs=None):
        """ Helper function """
        width = 5e-2
        tailScl = 5e-2
        muLtail = -tailScl*1./(y**(0.85))
        muRtail = tailScl*1./((1-y)**(0.85))
        slpScl = 0.45
        muLlin = slpScl*Omga*4*(0.26-y)*step_down(y, 0.5, width)
        muRlin = (slpScl*Omga*4*(0.74-y) + Omgb)*step_up(y, 0.5, width)
        muR = muLtail + muRtail + muLlin + muRlin
        return muR

    def graphite_1param_homog_2(self, y, Omga, Omgb, ISfuncs=None):
        """ Helper function """
        width = 5e-2
        tailScl = 5e-2
        slpScl = 0.45
        muLtail = -tailScl*1./(y**(0.85))
        muRtail = tailScl*1./((1-y)**(0.85))
        muLlin = (slpScl*Omga*12*(0.40-y)
                  * step_down(y, 0.49, 0.9*width)*step_up(y, 0.35, width))
        muRlin = (slpScl*Omga*4*(0.74-y) + Omgb)*step_up(y, 0.5, width)
        muLMod = (0.
                  + 40*(-np.exp(-y/0.015))
                  + 0.75*(np.tanh((y-0.17)/0.02) - 1)
                  + 1.0*(np.tanh((y-0.22)/0.040) - 1)
                  )*step_down(y, 0.35, width)
        muR = muLMod + muLtail + muRtail + muLlin + muRlin
        return muR

    def graphite_1param_homog_3(self, y, Omga, Omgb, ISfuncs=None):
        """ Helper function with low hysteresis and soft tail """
        width = 5e-2
        tailScl = 5e-2
        muLtail = -tailScl*1./(y**(0.85))
        muRtail = tailScl*1./((1-y)**(0.85))
        muRtail = 1.0e1*step_up(y, 1.0, 0.045)
        muLlin = (0.15*Omga*12*(0.40-y**0.98)
                  * step_down(y, 0.49, 0.9*width)*step_up(y, 0.35, width))
        muRlin = (0.1*Omga*4*(0.74-y) + 0.90*Omgb)*step_up(y, 0.5, 0.4*width)
        muLMod = (0.
                  + 40*(-np.exp(-y/0.015))
                  + 0.75*(np.tanh((y-0.17)/0.02) - 1)
                  + 1.0*(np.tanh((y-0.22)/0.040) - 1)
                  )*step_down(y, 0.35, width)
        muR = 0.18 + muLMod + muLtail + muRtail + muLlin + muRlin
        return muR

    def non_homog_rect_fixed_csurf(self, y, ybar, B, kappa, ywet):
        """ Helper function """
        N = len(y)
        ytmp = np.empty(N+2, dtype=object)
        ytmp[1:-1] = y
        ytmp[0] = ywet
        ytmp[-1] = ywet
        dxs = 1./N
        curv = np.diff(ytmp, 2)/(dxs**2)
        muR_nh = -kappa*curv + B*(y - ybar)
        return muR_nh

    def non_homog_round_wetting(self, y, ybar, B, kappa, beta_s, shape, r_vec):
        """ Helper function """
        dr = r_vec[1] - r_vec[0]
        Rs = 1.
        curv = geo.calc_curv(y, dr, r_vec, Rs, beta_s, shape)
        muR_nh = B*(y - ybar) - kappa*curv
        return muR_nh

    def general_non_homog(self, y, ybar):
        """ Helper function """
        ptype = self.ndD["type"]
        mod1var, mod2var = False, False
        if isinstance(y, np.ndarray):
            mod1var = True
            N = len(y)
        elif (isinstance(y, tuple) and len(y) == 2
                and isinstance(y[0], np.ndarray)):
            mod2var = True
            N = len(y[0])
        else:
            raise Exception("Unknown input type")
        if ("homog" not in ptype) and (N > 1):
            shape = self.ndD["shape"]
            kappa = self.ndD["kappa"]
            B = self.ndD["B"]
            if shape == "C3":
                if mod1var:
                    cwet = self.ndD["cwet"]
                    muR_nh = self.non_homog_rect_fixed_csurf(
                        y, ybar, B, kappa, cwet)
                elif mod2var:
                    raise NotImplementedError("no 2param C3 model known")
            elif shape in ["cylinder", "sphere"]:
                beta_s = self.ndD["beta_s"]
                r_vec = geo.get_unit_solid_discr(shape, N)[0]
                if mod1var:
                    muR_nh = self.non_homog_round_wetting(
                        y, ybar, B, kappa, beta_s, shape, r_vec)
                elif mod2var:
                    muR1_nh = self.non_homog_round_wetting(
                        y[0], ybar[0], B, kappa, beta_s, shape, r_vec)
                    muR2_nh = self.non_homog_round_wetting(
                        y[1], ybar[1], B, kappa, beta_s, shape, r_vec)
                    muR_nh = (muR1_nh, muR2_nh)
        else:  # homogeneous particle
            if mod1var:
                muR_nh = 0*y
            elif mod2var:
                muR_nh = (0*y[0], 0*y[1])
        return muR_nh


def step_down(x, xc, delta):
    return 0.5*(-np.tanh((x - xc)/delta) + 1)


def step_up(x, xc, delta):
    return 0.5*(np.tanh((x - xc)/delta) + 1)

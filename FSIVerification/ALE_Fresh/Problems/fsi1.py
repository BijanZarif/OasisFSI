from dolfin import *
import numpy as np
"""
from Utils.argpar import *

args = parse()
v_deg = args.v_deg
p_deg = args.p_deg
d_deg = args.d_deg
dt = args.dt
"""
mesh_file = Mesh("Mesh/fluid_new.xml")
#mesh_file = refine(mesh_file)
#Parameters for each numerical case
common = {"mesh": mesh_file,
          "v_deg": 2,    #Velocity degree
          "p_deg": 1,    #Pressure degree
          "d_deg": 2,    #Deformation degree
          "T": 8,          # End time
          "dt": 0.5,       # Time step
          "rho_f": 1.0E3,    #
          "mu_f": 1.,
          "rho_s" : Constant(1.0E3),
          "mu_s" : Constant(0.5E6),
          "nu_s" : Constant(0.4),
          "Um" : 0.2,
          "D" : 0.1,
          "H" : 0.41,
          "L" : 2.5
     }

vars().update(common)
lamda_s = nu_s*2*mu_s/(1 - 2.*nu_s)
#plot(mesh, interactive=True)

for coord in mesh.coordinates():
    if coord[0]==0.6 and (0.199<=coord[1]<=0.2001): # to get the point [0.2,0.6] end of bar
        print coord
        break
# BOUNDARIES

#NOS = AutoSubDomain(lambda x: "on_boundary" and( near(x[1],0) or near(x[1], 0.41)))
Inlet = AutoSubDomain(lambda x: "on_boundary" and near(x[0],0))
Outlet = AutoSubDomain(lambda x: "on_boundary" and (near(x[0],2.5)))
Wall =  AutoSubDomain(lambda x: "on_boundary" and (near(x[1], 0.41) or near(x[1], 0)))
Bar = AutoSubDomain(lambda x: "on_boundary" and (near(x[1], 0.21)) or near(x[1], 0.19) or near(x[0], 0.6 ) )
Circle =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  ))
Barwall =  AutoSubDomain(lambda x: "on_boundary" and (( (x[0] - 0.2)*(x[0] - 0.2) + (x[1] - 0.2)*(x[1] - 0.2)  < 0.0505*0.0505 )  and x[1]>=0.19 and x[1]<=0.21 and x[0]>0.2 ))

Allboundaries = DomainBoundary()

boundaries = FacetFunction("size_t",mesh_file)
boundaries.set_all(0)
Allboundaries.mark(boundaries, 1)
Wall.mark(boundaries, 2)
Inlet.mark(boundaries, 3)
Outlet.mark(boundaries, 4)
Bar.mark(boundaries, 5)
Circle.mark(boundaries, 6)
Barwall.mark(boundaries, 7)
#plot(boundaries,interactive=True)

ds = Measure("ds", subdomain_data = boundaries)
dS = Measure("dS", subdomain_data = boundaries)
n = FacetNormal(mesh_file)

Bar_area = AutoSubDomain(lambda x: (0.19 <= x[1] <= 0.21) and 0.24<= x[0] <= 0.6) # only the "flag" or "bar"
domains = CellFunction("size_t", mesh_file)
domains.set_all(1)
Bar_area.mark(domains, 2) #Overwrites structure domain
dx = Measure("dx", subdomain_data = domains)
#plot(domains,interactive = True)
dx_f = dx(1, subdomain_data = domains)
dx_s = dx(2, subdomain_data = domains)
dis_x = []
dis_y = []
Drag_list = []
Lift_list = []
#Fluid properties

class Inlet(Expression):
    def __init__(self, Um):
        self.t = 0
        self.U_in = Um
    def eval(self,value,x):
    	value[0] = 0.5*(1-np.cos(self.t*np.pi/2))*1.5*self.U_in*x[1]*(H-x[1])/((H/2.0)**2)
    	value[1] = 0
    def value_shape(self):
    	return (2,)

inlet = Inlet(Um)

def create_bcs(DVP, dvp_, n, k, Um, H, boundaries, Inlet, **semimp_namespace):
    #Fluid velocity conditions
    u_inlet  = DirichletBC(DVP.sub(1), inlet, boundaries, 3)
    u_wall   = DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 2)
    u_circ   = DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 6) #No slip on geometry in fluid
    u_barwall= DirichletBC(DVP.sub(1), ((0.0, 0.0)), boundaries, 7) #No slip on geometry in fluid

    #Pressure Conditions
    p_out = DirichletBC(DVP.sub(2), 0, boundaries, 4)

    bcs = [u_inlet, u_wall, u_circ, u_barwall, p_out]

    #Second type of BC
    print DVP.num_sub_spaces()
    if DVP.num_sub_spaces() == 4:
        print "IFTEST sb = 4"
        w_wall    = DirichletBC(DVP.sub(0).sub(1), (0.0), boundaries, 2)
        w_inlet   = DirichletBC(DVP.sub(0).sub(0), (0.0), boundaries, 3)
        w_outlet  = DirichletBC(DVP.sub(0).sub(0), (0.0), boundaries, 4)
        w_circle  = DirichletBC(DVP.sub(0).sub(1), (0.0), boundaries, 6)
        w_barwall = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 7) #No slip on geometry in fluid

        d_wall    = DirichletBC(DVP.sub(0).sub(1), (0.0), boundaries, 2)
        d_inlet   = DirichletBC(DVP.sub(0).sub(0), (0.0), boundaries, 3)
        d_outlet  = DirichletBC(DVP.sub(0).sub(0), (0.0), boundaries, 4)
        d_circle  = DirichletBC(DVP.sub(0).sub(1), (0.0), boundaries, 6)
        d_barwall = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 7)

        for i in [w_wall, w_inlet, w_outlet, w_circle, w_barwall, \
                  d_wall, d_inlet, d_outlet, d_circle, d_barwall]:
            bcs.append(i)
    #Ordinary BC
    else:
        print "Ordinary BC"
        #displacement conditions:
        d_wall    = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 2)
        d_inlet   = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 3)
        d_outlet  = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 4)
        d_circle  = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 6)
        d_barwall = DirichletBC(DVP.sub(0), ((0.0, 0.0)), boundaries, 7) #No slip on geometry in fluid
        for i in [d_wall, d_inlet, d_outlet, d_circle, d_barwall]:
            bcs.append(i)







    return dict(bcs = bcs, inlet = inlet)

def pre_solve(t, inlet, **semimp_namespace):
    if t < 2:
        inlet.t = t
    else:
        inlet.t = 2

    return dict(inlet = inlet)

def initiate(**monolithic):
    tic()
    return {}

def after_solve(t, dvp_, n,coord,dis_x,dis_y,Drag_list,Lift_list, **semimp_namespace):
    d = dvp_["n"].sub(0, deepcopy=True)
    v = dvp_["n"].sub(1, deepcopy=True)
    p = dvp_["n"].sub(2, deepcopy=True)
    #d, v, p = dvp_["n"].split(True)

    def F_(U):
    	return (Identity(len(U)) + grad(U))

    def J_(U):
    	return det(F_(U))

    def sigma_f_new(v, p, d, mu_f):
    	return -p*Identity(len(v)) + mu_f*(grad(v)*inv(F_(d)) + inv(F_(d)).T*grad(v).T)

    #Fx = -assemble((sigma_f_new(v, p, d, mu_f)*n)[0]*ds(6))
    #Fy = -assemble((sigma_f_new(v, p, d, mu_f)*n)[1]*ds(6))
    #Fx += -assemble(((-p("-")*Identity(len(v)) + mu_f*(grad(v)("-")*inv(F_(d("-"))) + inv(F_(d("-"))).T*grad(v)("-").T))*n('-'))[0]*dS(5))
    #Fy += -assemble(((-p("-")*Identity(len(v)) + mu_f*(grad(v)("-")*inv(F_(d("-"))) + inv(F_(d("-"))).T*grad(v)("-").T))*n('-'))[1]*dS(5))
    Dr = -assemble((sigma_f_new(v,p,d,mu_f)*n)[0]*ds(6))
    Li = -assemble((sigma_f_new(v,p,d,mu_f)*n)[1]*ds(6))
    Dr += -assemble((sigma_f_new(v("-"),p("-"),d("-"),mu_f)*n("-"))[0]*dS(5))
    Li += -assemble((sigma_f_new(v("-"),p("-"),d("-"),mu_f)*n("-"))[1]*dS(5))
    Drag_list.append(Dr)
    Lift_list.append(Li)

    print "LIFT = %g,  DRAG = %g" % (Li, Dr)

    dsx = d(coord)[0]
    dsy = d(coord)[1]
    dis_x.append(dsx)
    dis_y.append(dsy)
    print "dis_x/dis_y : %g %g "%(dsx,dsy)

    return {}

def post_process(T,dt,dis_x,dis_y, Drag_list,Lift_list, **semimp_namespace):
    print "End time ", toc()
    """
    time_list = np.linspace(0,T,T/dt+1)
    plt.plot(time_list,dis_x); plt.ylabel("Displacement x");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-1/P-"+str(v_deg) +"/dt-"+str(dt)+"/dis_x.png")
    plt.show()
    plt.plot(time_list,dis_y);plt.ylabel("Displacement y");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-1/P-"+str(v_deg) +"/dt-"+str(dt)+"/dis_y.png")
    plt.show()
    plt.plot(time_list,Drag);plt.ylabel("Drag");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-1/P-"+str(v_deg) +"/dt-"+str(dt)+"/drag.png")
    plt.show()
    plt.plot(time_list,Lift);plt.ylabel("Lift");plt.xlabel("Time");plt.grid();
    #plt.savefig("FSI_results/FSI-1/P-"+str(v_deg) +"/dt-"+str(dt)+"/lift.png")
    plt.show()
    """
    return {}

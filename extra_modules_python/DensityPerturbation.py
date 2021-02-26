import radiopropa as RP
import numpy as np
from radiotools import helper as hp
#from ObserverPlane import ObserverPlane 


class PerturbationLayer(RP.Module):
    """
    A layer a radiopropa surface.
    Part of a candidate crossing the layer is reflected. 
    Future propagation in scalar field will take care of directivity change automatically???
    """
    def __init__(self, surface, thickness, treshold=0.01):
        RP.Module.__init__(self)
        self.__surface = surface
        self.__thickness = thickness 
        self.__treshold = treshold

    def process(self, candidate):

        currentDistance = self.__surface.distance(candidate.current.getPosition())
        previousDistance = self.__surface.distance(candidate.previous.getPosition())
        
        launch_vector = [candidate.getLaunchVector().x, 
                        candidate.getLaunchVector().y, 
                        candidate.getLaunchVector().z]
        launch_dir = hp.cartesian_to_spherical(*launch_vector)

        #if (launch_dir[0]-60*RP.deg) < 1*RP.deg: print(currentDistance/RP.meter)
        current_inbetween = (abs(currentDistance) <= self.__thickness/2)
        previous_inbetween = (abs(previousDistance) <= self.__thickness/2)

        if current_inbetween and previous_inbetween:
            normal = self.__surface.normal(candidate.current.getPosition())
            v = candidate.current.getDirection()
            cos_theta = v.dot(normal)
            if abs(cos_theta) < self.__treshold:
                u = normal * (cos_theta*v.getR())
                self.new_direction = (v - u) / (v-u).getR() #new direction parallel to layer
                candidate.current.setDirection(self.new_direction)

                #Propagation module bends the ray slightly downwards,
                #resulting in a straigt line with a small negative slope
                #with respect to the layer. Adjusting for the position 
                #overcomes this.
                self.position_correction(candidate)

            else:
                pass
            candidate.limitNextStep(abs(abs(currentDistance)-self.__thickness/2))

        else:
            candidate.limitNextStep(abs(abs(currentDistance)-self.__thickness/2))

    def position_correction(self, candidate):
        p = candidate.previous.getPosition()
        c = candidate.current.getPosition()
        step_size = (c-p).getR()
        new_position = c + self.new_direction*step_size
        candidate.current.setPosition(new_position)

    def get_cos_theta(self, position, direction):
        normal = self.__surface.normal(position)
        return direction.dot(normal)

    def get_distance(self, position):
        return self.__surface.distance(position)

    def get_thickness(self):
        return self.__thickness

    def get_threshold(self):
        return self.__treshold


class PerturbationHorizontal(PerturbationLayer):
    def __init__(self,z,thickness):
        layer_pos = RP.Vector3d(0,0,z)
        surface = RP.Plane(layer_pos, RP.Vector3d(0,0,1))
        PerturbationLayer.__init__(self, surface, thickness)

    def position_correction(self, candidate):
        p = candidate.previous.getPosition()
        c = candidate.current.getPosition()
        new_position = RP.Vector3d(c.x,c.y,p.z)
        candidate.current.setPosition(new_position)
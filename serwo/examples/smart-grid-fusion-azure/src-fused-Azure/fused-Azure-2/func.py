
from memstress_128MB_25KB import func as TaskB
from resnet_25KB import func as TaskC
from xmlparse_23KB_25KB import func as TaskA

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    otte = TaskA.function(serwoObject)
    otte.set_basepath(serwoObject.get_basepath())
    ligl = TaskB.function(otte)
    ligl.set_basepath(otte.get_basepath())
    ttru = TaskC.function(ligl)
    ttru.set_basepath(ligl.get_basepath())
    return ttru

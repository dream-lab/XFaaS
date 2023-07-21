
from memstress_128MB_25KB import func as TaskB
from resnet_25KB import func as TaskC
from xmlparse_23KB_25KB import func as TaskA

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    oudw = TaskA.function(serwoObject)
    oudw.set_basepath(serwoObject.get_basepath())
    fdhb = TaskB.function(oudw)
    fdhb.set_basepath(oudw.get_basepath())
    tayr = TaskC.function(fdhb)
    tayr.set_basepath(fdhb.get_basepath())
    return tayr

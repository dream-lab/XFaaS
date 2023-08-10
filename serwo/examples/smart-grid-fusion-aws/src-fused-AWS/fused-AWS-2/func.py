
from memstress_128MB_25KB import func as TaskB
from resnet_25KB import func as TaskC
from xmlparse_23KB_25KB import func as TaskA

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    clyf = TaskA.function(serwoObject)
    clyf.set_basepath(serwoObject.get_basepath())
    wsse = TaskB.function(clyf)
    wsse.set_basepath(clyf.get_basepath())
    bbnp = TaskC.function(wsse)
    bbnp.set_basepath(wsse.get_basepath())
    return bbnp

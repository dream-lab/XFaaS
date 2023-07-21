
from memstress_128MB_25KB import func as TaskE
from xmlparse_23KB_25KB import func as TaskF

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    bdkd = TaskE.function(serwoObject)
    bdkd.set_basepath(serwoObject.get_basepath())
    tmzg = TaskF.function(bdkd)
    tmzg.set_basepath(bdkd.get_basepath())
    return tmzg

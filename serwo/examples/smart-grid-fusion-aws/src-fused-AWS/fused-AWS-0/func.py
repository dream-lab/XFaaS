from memstress_128MB_25KB import func as TaskE
from xmlparse_23KB_25KB import func as TaskF

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:
    iygv = TaskE.function(serwoObject)
    iygv.set_basepath(serwoObject.get_basepath())
    emov = TaskF.function(iygv)
    emov.set_basepath(iygv.get_basepath())
    return emov

from xmlparse_23KB_25KB import func as TaskF
from memstress_128MB_25KB import func as TaskE

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:
    xrnp = TaskE.function(serwoObject)
    xrnp.set_basepath(serwoObject.get_basepath())
    axjs = TaskF.function(xrnp)
    axjs.set_basepath(xrnp.get_basepath())
    return axjs

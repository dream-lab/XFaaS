from resnet_25KB import func as TaskL
from resnet_25KB import func as TaskP
from xmlparse_23KB_25KB import func as TaskQ

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:
    lbsu = TaskL.function(serwoObject)
    lbsu.set_basepath(serwoObject.get_basepath())
    dstt = TaskP.function(lbsu)
    dstt.set_basepath(lbsu.get_basepath())
    epjt = TaskQ.function(dstt)
    epjt.set_basepath(dstt.get_basepath())
    return epjt

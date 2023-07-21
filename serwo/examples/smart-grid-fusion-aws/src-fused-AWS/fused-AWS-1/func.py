
from xmlparse_23KB_25KB import func as TaskQ
from resnet_25KB import func as TaskL
from resnet_25KB import func as TaskP

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    cbgz = TaskL.function(serwoObject)
    cbgz.set_basepath(serwoObject.get_basepath())
    kpvo = TaskP.function(cbgz)
    kpvo.set_basepath(cbgz.get_basepath())
    vrcr = TaskQ.function(kpvo)
    vrcr.set_basepath(kpvo.get_basepath())
    return vrcr

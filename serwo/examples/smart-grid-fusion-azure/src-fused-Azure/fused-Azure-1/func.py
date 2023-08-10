
from resnet_25KB import func as TaskP
from xmlparse_23KB_25KB import func as TaskQ
from resnet_25KB import func as TaskL

from python.src.utils.classes.commons.serwo_objects import SerWOObject, SerWOObjectsList


def function(serwoObject) -> SerWOObject:

    jiaf = TaskL.function(serwoObject)
    jiaf.set_basepath(serwoObject.get_basepath())
    pvex = TaskP.function(jiaf)
    pvex.set_basepath(jiaf.get_basepath())
    agdj = TaskQ.function(pvex)
    agdj.set_basepath(pvex.get_basepath())
    return agdj

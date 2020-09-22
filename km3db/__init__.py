from pkg_resources import get_distribution, DistributionNotFound

version = get_distribution(__name__).version


from .core import DBManager
from .tools import StreamDS

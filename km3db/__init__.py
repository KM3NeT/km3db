from pkg_resources import get_distribution, DistributionNotFound

version = get_distribution(__name__).version


from .core import DBManager, AuthenticationError
from .tools import StreamDS, CLBMap

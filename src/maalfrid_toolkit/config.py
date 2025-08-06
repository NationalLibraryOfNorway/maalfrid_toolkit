import os
from dotenv import load_dotenv

load_dotenv()

crawl_id = 1
num_parallel_processes = 5

# Justext options
MAX_LINK_DENSITY = 0.4
MAX_HEADING_DISTANCE = 150
LENGTH_LOW = 70
LENGTH_HIGH = 200
STOPWORDS_LOW = 0.30
STOPWORDS_HIGH = 0.32
NO_HEADINGS = False

# DIR
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.dirname(os.path.abspath(__file__))
JUSTEXT_STOPLISTS_DIR = os.path.join(current_dir, 'models/stoplists_justext/')

# Other
LANGUAGE_FILTER_DIR = os.path.join(current_dir, 'models/language_filter/')
SUPPORTED_CONTENT_TYPES = ['text/html', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.oasis.opendocument.text-master']

# crawler options
user_agent = os.getenv("MAALFRID_TOOLKIT_USER_AGENT", "test-agent")
prefix = os.getenv("MAALFRID_TOOLKIT_CRAWL_PREFIX", "test-prefix")
crawlhost = os.getenv("MAALFRID_TOOLKIT_CRAWL_HOST", 'localhost')

# DB options (use environment variables)
database = os.getenv("MAALFRID_TOOLKIT_POSTGRES_DB", "")
host = os.getenv("MAALFRID_TOOLKIT_POSTGRES_HOST", "")
port = os.getenv("MAALFRID_TOOLKIT_POSTGRES_PORT", "")
user = os.getenv("MAALFRID_TOOLKIT_POSTGRES_USER", "")
password = os.getenv("MAALFRID_TOOLKIT_POSTGRES_PASSWORD", "")
sslmode = os.getenv("MAALFRID_TOOLKIT_POSTGRES_SSLMODE", "")
sslrootcert = os.getenv("MAALFRID_TOOLKIT_POSTGRES_SSLROOTCERT", "")
sslcert = os.getenv("MAALFRID_TOOLKIT_POSTGRES_SSLCERT", "")
sslkey = os.getenv("MAALFRID_TOOLKIT_POSTGRES_SSLKEY", "")

# stopword filter
stopword_filters = ['Arabic', 'Danish', 'German', 'English', 'Estonian', 'Persian', 'Finnish', 'French', 'Icelandic', 'Italian', 'Norwegian_NRK', 'Norwegian_NRK', 'Polish', 'Romanian', 'Russian', 'sma', 'sme', 'smj', 'smn', 'sms', 'Somali', 'Spanish', 'Swedish', 'Turkish', 'Urdu', 'Vietnamese']

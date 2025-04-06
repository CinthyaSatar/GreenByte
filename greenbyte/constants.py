"""
Constants used throughout the GreenByte application.
"""

# Plant Status Constants
DEFAULT_PLANT_STATUSES = ['Seedling', 'Growing', 'Mature', 'Harvesting']

# Plant Status Icons
PLANT_STATUS_ICONS = {
    'Seedling': 'seedling',
    'Growing': 'leaf',
    'Mature': 'tree',
    'Harvesting': 'cut',
    'Dormant': 'moon',
    'Flowering': 'flower',
    'Fruiting': 'apple-alt',
    'Transplanted': 'exchange-alt',
    'Diseased': 'biohazard',
    'Completed': 'check-circle'
}

# Order Status Constants
ORDER_STATUSES = ['pending', 'processing', 'completed', 'cancelled']
ORDER_FREQUENCIES = ['weekly', 'monthly']

# User Role Constants
USER_ROLES = ['member', 'commercial', 'manager']

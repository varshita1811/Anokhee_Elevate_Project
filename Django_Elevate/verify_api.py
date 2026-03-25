import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from elevate.views import get_nominee_summary_view
from elevate.models import TeamMembersTable, NominationsTable, AwardsTable, TeamsTable, ARTTable, SprintTable
from elevate.models import User
import uuid

# Helper to print stuff
def print_separator(msg):
    print(f"\n{'='*20} {msg} {'='*20}\n")

# Setup a dummy request
rf = RequestFactory()
request = rf.get('/api/nominee-summary/')
# We need an authenticated user to pass IsAuthenticated permission.
# We will bypass permissions for this quick test by manually instantiating the view 
# and replacing permission_classes, or just calling the get method directly.

view = get_nominee_summary_view()
view.permission_classes = [] # bypass

# Try without nominee_id
print_separator("Testing missing nominee_id")
response = view.get(request)
print("Status:", response.status_code)
print("Data:", response.data)

# Try with invalid nominee_id
print_separator("Testing invalid nominee_id")
request = rf.get('/api/nominee-summary/?nominee_id=00000000-0000-0000-0000-000000000000')
response = view.get(request)
print("Status:", response.status_code)
print("Data:", response.data)

# Let's find a valid nominee_id if any nominations exist
nomination = NominationsTable.objects.first()
if nomination:
    valid_nominee_id = nomination.nominee.employee_id
    print_separator(f"Testing valid nominee_id with comments: {valid_nominee_id}")
    
    # Check how many comments they have
    noms = NominationsTable.objects.filter(nominee__employee_id=valid_nominee_id)
    print("Found comments count:", noms.count())
    
    request = rf.get(f'/api/nominee-summary/?nominee_id={valid_nominee_id}')
    response = view.get(request)
    print("Status:", response.status_code)
    print("Data:", response.data)
else:
    print_separator("No nominations found in DB to test complete flow.")
    
print_separator("Test complete")

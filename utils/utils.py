from rest_framework.response import Response
from django.core.serializers.json import DjangoJSONEncoder
import json

def create_response(success: bool, message: str, status_code: int, **kwargs):
    content = {
        'success': success,
        'message': message,
        **kwargs
    }
    serialized_content = json.dumps(content, cls=DjangoJSONEncoder) 
    return Response(data=json.loads(serialized_content), status=status_code)

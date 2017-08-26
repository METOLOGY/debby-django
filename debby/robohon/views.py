import json

import apiai
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from debby import settings
from line.handler import ApiAiData
import socket

@csrf_exempt
def robohon(request):
    if request.method == 'POST':
        address = ('192.168.1.171', 5123)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(address)

        json_data = json.loads(request.body.decode('utf-8'))

        api_ai = apiai.ApiAI(settings.CLIENT_ACCESS_TOKEN)
        request = api_ai.text_request()
        request.session_id = 'robohon'
        request.query = json_data['context']
        response = request.getresponse()
        ai_data = ApiAiData(response)
        s.bind(address)
        s.sendto('{"@STEP": "0", "@SPEECH": "{}", "@MOTIONID": "general"}'.format(ai_data.response_text).encode('utf-8'), address)

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

# def home(request):
#     return HttpResponse("Welcome to the Spellcast API!")

@api_view(['GET'])
def home(request):
    return Response({"status": "ok", "message": "API Spellcast activa"}, status=200)

def test(request):
    return HttpResponse("Test endpoint is working!")
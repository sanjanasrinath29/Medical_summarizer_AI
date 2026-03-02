from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import MedicalReport, ChatMessage
from .rag_engine import (
    extract_text_from_pdf,
    build_report_vectorstore,
    generate_summary,
    answer_question
)


def index(request):
    return render(request, 'index.html')


class UploadReportView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'Please upload a PDF file'},
                status=400
            )

        if not file.name.endswith('.pdf'):
            return Response(
                {'error': 'Only PDF files are supported'},
                status=400
            )

        # Save file to database
        report = MedicalReport.objects.create(
            file=file,
            status='processing'
        )

        try:
            # Step 1 — Extract text from PDF
            text = extract_text_from_pdf(report.file.path)
            report.original_text = text
            report.save()

            # Step 2 — Store report in ChromaDB
            build_report_vectorstore(text, str(report.id))

            # Step 3 — Generate summary using
            #           report + knowledge base
            summary = generate_summary(text, str(report.id))
            report.summary = summary
            report.status = 'done'
            report.save()

            return Response({
                'report_id': str(report.id),
                'summary': summary,
                'status': 'done'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()  # prints full error in terminal
            report.status = 'failed'
            report.save()
            return Response({'error': str(e)}, status=500)


class AskQuestionView(APIView):

    def post(self, request, report_id):
        question = request.data.get('question')

        if not question:
            return Response(
                {'error': 'Please provide a question'},
                status=400
            )

        try:
            report = MedicalReport.objects.get(
                id=report_id,
                status='done'
            )
        except MedicalReport.DoesNotExist:
            return Response(
                {'error': 'Report not found'},
                status=404
            )

        # Get answer from RAG engine
        answer = answer_question(str(report.id), question)

        # Save to chat history
        ChatMessage.objects.create(
            report=report,
            user_message=question,
            ai_response=answer
        )

        return Response({'answer': answer})
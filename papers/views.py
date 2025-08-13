import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase import create_client, Client
from dotenv import load_dotenv


def transform_to_nested(all_files_data):
    result = {"subjects": []}

    # Step 1: Group by (subject_code, subject_name, year)
    subject_groups = {}

    for file_data in all_files_data:
        # Create a unique key for each subject+year combination
        key = (file_data['subject_code'], file_data['subject_name'], file_data['year'])

        if key not in subject_groups:
            subject_groups[key] = []

        subject_groups[key].append(file_data)

    # Step 2: For each subject+year group, build the nested structure
    for (subject_code, subject_name, year), files in subject_groups.items():

        subject_obj = {
            "subject_name": subject_name,
            "subject_code": subject_code,
            "year": year,
            "sessions": {}
        }

        # Step 3: Build sessions/papers/variants for this subject
        for file_data in files:
            session = file_data['session']
            paper = file_data['paper']
            variant = file_data['variant']
            doc_type = file_data['doc_type']
            url = file_data['file_url']

            # Ensure session exists
            if session not in subject_obj["sessions"]:
                subject_obj["sessions"][session] = {"papers": {}}

            # Ensure paper exists
            if paper not in subject_obj["sessions"][session]["papers"]:
                subject_obj["sessions"][session]["papers"][paper] = {"variants": {}}

            # Ensure variant exists
            if variant not in subject_obj["sessions"][session]["papers"][paper]["variants"]:
                subject_obj["sessions"][session]["papers"][paper]["variants"][variant] = {"doc_types": {}}

            # Add the doc_type and URL
            subject_obj["sessions"][session]["papers"][paper]["variants"][variant]["doc_types"][doc_type] = url

        result["subjects"].append(subject_obj)

    for subject in result["subjects"]:
        for session_key, session in subject["sessions"].items():
            for paper_key, paper in session["papers"].items():
                for variant_key, variant in paper["variants"].items():
                    # Sort doc_types: qp first, then ms
                    sorted_docs = {}
                    if 'qp' in variant["doc_types"]:
                        sorted_docs['qp'] = variant["doc_types"]['qp']
                    if 'ms' in variant["doc_types"]:
                        sorted_docs['ms'] = variant["doc_types"]['ms']

                    variant["doc_types"] = sorted_docs

    return result

load_dotenv()

# Supabase setup
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)


def get_papers(request, subject, year):
    try:
        # Query Supabase for specific subject and year
        response = supabase.table("past-papers").select("*").eq("subject_name", subject).eq("year", year).execute()

        if not response.data:
            return JsonResponse({"error": "No papers found"}, status=404)

        # Transform the data using your existing function
        nested_data = transform_to_nested(response.data)

        return JsonResponse(nested_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

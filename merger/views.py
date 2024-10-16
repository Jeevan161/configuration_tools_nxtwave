# merger/views.py
import zipfile
import os
import shutil
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings


def merge_zip_files(zip_files, output_name):
    # Creating a temporary directory to store the merged files
    temp_merge_dir = os.path.join(settings.MEDIA_ROOT, 'temp_merged')
    if not os.path.exists(temp_merge_dir):
        os.makedirs(temp_merge_dir)

    for zip_file in zip_files:
        # Save the uploaded file temporarily
        temp_file_path = os.path.join(settings.MEDIA_ROOT, zip_file.name)
        with open(temp_file_path, 'wb+') as destination:
            for chunk in zip_file.chunks():
                destination.write(chunk)

        temp_extract_dir = os.path.join(settings.MEDIA_ROOT, 'temp_extract_' + zip_file.name)
        if not os.path.exists(temp_extract_dir):
            os.makedirs(temp_extract_dir)

        # Extract the current zip file
        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        # Walk through the extracted files and merge the content
        for dirpath, dirnames, filenames in os.walk(temp_extract_dir):
            for filename in filenames:
                src_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(src_path, temp_extract_dir)
                dest_path = os.path.join(temp_merge_dir, relative_path)

                # Create directories if they don't exist
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # If the file is a JSON file and exists in the target, merge the JSON data
                if os.path.exists(dest_path) and filename.endswith('.json'):
                    with open(dest_path, 'r') as existing_file, open(src_path, 'r') as new_file:
                        existing_data = json.load(existing_file)
                        new_data = json.load(new_file)

                        # Merge logic: append lists or combine dictionaries
                        if isinstance(existing_data, list) and isinstance(new_data, list):
                            merged_data = existing_data + new_data
                        elif isinstance(existing_data, dict) and isinstance(new_data, dict):
                            merged_data = {**existing_data, **new_data}
                        else:
                            merged_data = existing_data

                    # Write the merged content
                    with open(dest_path, 'w') as output_file:
                        json.dump(merged_data, output_file, indent=4)
                else:
                    # If it's not a JSON file or the file doesn't exist, just copy it
                    shutil.copy(src_path, dest_path)

        # Clean up the extracted directory
        shutil.rmtree(temp_extract_dir)
        os.remove(temp_file_path)

    # Create the final merged zip file with the provided name
    output_zip_name = f"{output_name}.zip"
    output_zip_path = os.path.join(settings.MEDIA_ROOT, output_zip_name)

    with zipfile.ZipFile(output_zip_path, 'w') as merged_zip:
        for dirpath, dirnames, filenames in os.walk(temp_merge_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                arcname = os.path.relpath(file_path, temp_merge_dir)
                merged_zip.write(file_path, arcname)

    # Clean up the merged directory
    shutil.rmtree(temp_merge_dir)

    return output_zip_path


def upload_and_merge_zips(request):
    if request.method == 'POST':
        zip_files = request.FILES.getlist('zip_files')  # Multiple zip files
        output_name = request.POST.get('output_name')  # Output zip name from user

        if zip_files and output_name:
            output_zip_path = merge_zip_files(zip_files, output_name)
            # Serve the merged zip file for download
            with open(output_zip_path, 'rb') as merged_file:
                response = HttpResponse(merged_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{output_name}.zip"'
                return response

    return render(request, 'upload.html')


def rename_json_files_in_zip(zip_file, uuid_name, output_zip_name):
    temp_extract_dir = os.path.join(settings.MEDIA_ROOT, 'temp_extract')
    temp_output_dir = os.path.join(settings.MEDIA_ROOT, 'temp_output')

    # Create temp directories for extraction and output
    os.makedirs(temp_extract_dir, exist_ok=True)
    os.makedirs(temp_output_dir, exist_ok=True)

    # Extract the uploaded zip file
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    # Walk through the extracted files, retain structure, and rename JSON files
    for dirpath, dirnames, filenames in os.walk(temp_extract_dir):
        for filename in filenames:
            src_path = os.path.join(dirpath, filename)

            # Build the relative path (relative to the temp_extract_dir)
            relative_path = os.path.relpath(src_path, temp_extract_dir)
            dest_path = os.path.join(temp_output_dir, relative_path)

            # Create directories in the output directory (preserving folder structure)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # If it's a JSON file, rename it to {uuid_name}.json
            if filename.endswith('.json'):
                new_filename = f"{uuid_name}.json"
                dest_path = os.path.join(os.path.dirname(dest_path), new_filename)

            # Copy the file (renaming JSON files, preserving others)
            shutil.copy(src_path, dest_path)

    # Create the final zip file with renamed JSONs and the original structure
    output_zip_path = os.path.join(settings.MEDIA_ROOT, f"{output_zip_name}.zip")
    with zipfile.ZipFile(output_zip_path, 'w') as new_zip:
        for dirpath, dirnames, filenames in os.walk(temp_output_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                arcname = os.path.relpath(file_path, temp_output_dir)  # Retain folder structure in zip
                new_zip.write(file_path, arcname)

    # Cleanup temp directories
    shutil.rmtree(temp_extract_dir)
    shutil.rmtree(temp_output_dir)

    return output_zip_path


def upload_and_rename_jsons(request):
    if request.method == 'POST':
        zip_file = request.FILES['zip_file']
        uuid_name = request.POST['uuid_name']
        output_zip_name = request.POST['output_zip_name']

        # Process the uploaded zip and rename JSONs
        output_zip_path = rename_json_files_in_zip(zip_file, uuid_name, output_zip_name)

        # Serve the updated zip file for download
        with open(output_zip_path, 'rb') as updated_zip:
            response = HttpResponse(updated_zip.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{output_zip_name}.zip"'
            return response

    return render(request, 'rename_json.html')


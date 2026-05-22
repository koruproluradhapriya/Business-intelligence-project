from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from database.connection import find_one_by_id, get_collection
from services.csv_processor import process_file, SUPPORTED_EXTENSIONS
from services.analytics_service import compute_analytics
import os

from database.mongo import utcnow
from services.persistence_service import delete_upload_bundle, persist_upload_bundle

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = SUPPORTED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/dataset', methods=['POST'])
@upload_bp.route('/csv', methods=['POST'])
@jwt_required()
def upload_csv():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    upload_type = request.form.get('uploadType', 'auto')

    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Supported formats: CSV, XLSX, XLS, JSON, TSV, and Parquet."}), 400

    filename = secure_filename(file.filename)
    timestamp = utcnow().strftime('%Y%m%d_%H%M%S')
    saved_name = f"{user_id}_{timestamp}_{filename}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_name)

    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(save_path)

    # Process the file
    try:
        result = process_file(save_path, upload_type)
    except Exception as e:
        try:
            os.remove(save_path)
        except OSError:
            pass
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 422

    # Save upload record
    upload_doc = {
        "userId": user_id,
        "fileName": filename,
        "savedName": saved_name,
        "filePath": save_path,
        "fileType": filename.rsplit('.', 1)[1].lower(),
        "uploadType": upload_type,
        "rowCount": result['rowCount'],
        "columns": result['columns'],
        "schema": result['schema'],
        "columnProfiles": result.get('columnProfiles', []),
        "inferredSchema": result.get('inferredSchema', {}),
        "semanticGroups": result.get('semanticGroups', {}),
        "qualityReport": result.get('qualityReport', {}),
        "profileReport": result.get('profileReport', {}),
        "fileMetadata": result.get('fileMetadata', {}),
        "uploadedAt": utcnow(),
        "status": "processed",
    }
    upload_result = get_collection('uploads').insert_one(upload_doc)
    upload_id = str(upload_result.inserted_id)

    # Compute and save analytics
    try:
        analytics = compute_analytics(
            result['data'],
            upload_type,
            user_id,
            upload_id,
            dataset_name=filename,
            column_profiles=result.get('columnProfiles', []),
            quality_report=result.get('qualityReport', {}),
            inferred_schema=result.get('inferredSchema', {}),
            semantic_groups=result.get('semanticGroups', {}),
            file_metadata=result.get('fileMetadata', {}),
            profile_report=result.get('profileReport', {}),
        )
        analytics_doc = {
            "userId": user_id,
            "uploadId": upload_id,
            "uploadType": upload_type,
            **analytics,
            "createdAt": utcnow(),
        }
        get_collection('analytics').replace_one(
            {"userId": user_id, "uploadId": upload_id},
            analytics_doc,
            upsert=True
        )
        persist_upload_bundle(user_id, upload_id, upload_doc, analytics_doc)
    except Exception as e:
        current_app.logger.warning(f"Analytics computation warning: {e}")

    return jsonify({
        "message": "File uploaded and processed successfully",
        "uploadId": upload_id,
        "fileName": filename,
        "rowCount": result['rowCount'],
        "columns": result['columns'],
        "preview": result['preview'],
        "schema": result['schema'],
        "columnProfiles": result.get('columnProfiles', []),
        "inferredSchema": result.get('inferredSchema', {}),
        "semanticGroups": result.get('semanticGroups', {}),
        "qualityReport": result.get('qualityReport', {}),
        "profileReport": result.get('profileReport', {}),
        "fileMetadata": result.get('fileMetadata', {}),
    }), 201


@upload_bp.route('/history', methods=['GET'])
@jwt_required()
def upload_history():
    user_id = get_jwt_identity()
    uploads = list(get_collection('uploads').find(
        {"userId": user_id},
        {"filePath": 0, "savedName": 0}
    ).sort([("uploadedAt", -1)]).limit(20))

    for u in uploads:
        u['_id'] = str(u['_id'])
        u['uploadedAt'] = u['uploadedAt'].isoformat() if hasattr(u.get('uploadedAt'), 'isoformat') else ''

    return jsonify({"uploads": uploads})


@upload_bp.route('/<upload_id>', methods=['DELETE'])
@jwt_required()
def delete_upload(upload_id):
    user_id = get_jwt_identity()
    upload = find_one_by_id('uploads', upload_id, {"userId": user_id})
    if not upload:
        return jsonify({"error": "Upload not found"}), 404

    try:
        fp = upload.get('filePath', '')
        if fp and os.path.exists(fp):
            os.remove(fp)
    except OSError:
        pass

    delete_upload_bundle(user_id, upload_id)
    return jsonify({"message": "Upload deleted"})

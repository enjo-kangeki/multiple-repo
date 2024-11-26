import base64
import functions_framework
from flask import jsonify
import json
import uuid

from get_channel_report import get_channel_report
from settings import MAX_RESULTS, TermType, MAX_RETRIES
from utils import (
    check_valid_date,
    get_date_range_from_term_type,
    exponential_backoff,
    get_brand_name,
)
from logger import app_logger, make_log_fields


@functions_framework.cloud_event
def collectChannelPerformance(cloud_event):
    """Handle Pub/Sub messages."""
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode(
        "utf-8"
    )

    request_id = str(uuid.uuid4())
    log_fields = make_log_fields(
        request_id=request_id, func_name="collectChannelPerformance"
    )
    app_logger.info(
        "3ba82470-2982-44f8-b469-a9a11ac6dfd9",
        "Start collectChannelPerformance function",
        extra=log_fields,
    )

    try:
        request_json = json.loads(pubsub_message)
    except json.JSONDecodeError:
        app_logger.error(
            "e958944d-09b9-45c4-9951-86c644bff5f0",
            "Invalid JSON format.",
            extra=log_fields,
        )
        return jsonify({"error": "Invalid JSON format."}), 400

    channel_id = request_json.get("channel_id")
    term = request_json.get("term")
    start_date = request_json.get("start_date")
    end_date = request_json.get("end_date")
    channel_name = get_brand_name(channel_id)
    error_message = f"Channel {channel_name}, Error"

    if not (channel_id and (term or (start_date and end_date))):
        app_logger.error(
            "0d615f0f-ec35-485d-b0ce-bf12019b5d12",
            f"{error_message}: Missing required parameters.",
            extra=log_fields,
        )
        return jsonify({"error": "Missing required parameters."}), 400

    if start_date and not check_valid_date(start_date):
        app_logger.error(
            "3f7267c4-cdec-4ab8-809a-10c6eb10d7ce",
            f"{error_message}: Invalid start date format. Dates must be in YYYY-MM-DD.",
            extra=log_fields,
        )
        return (
            jsonify({"error": "Invalid date format. Dates must be in YYYY-MM-DD."}),
            400,
        )

    if end_date and not check_valid_date(end_date):
        app_logger.error(
            "fc9bc41f-aada-40a3-9c0d-8b09d4092bc6",
            f"{error_message}: Invalid end date format. Dates must be in YYYY-MM-DD.",
            extra=log_fields,
        )
        return (
            jsonify({"error": "Invalid date format. Dates must be in YYYY-MM-DD."}),
            400,
        )

    if term and term in [item.value for item in TermType]:
        start_date, end_date = get_date_range_from_term_type(term)

    start_index = 1
    max_results = MAX_RESULTS

    for attempt in range(MAX_RETRIES):
        try:
            get_channel_report(
                request_id,
                channel_id,
                channel_name,
                start_index,
                max_results,
                start_date,
                end_date,
            )
            return (
                jsonify(
                    {"success": f"Get channel perfomrmance by {term} successfully"}
                ),
                200,
            )
        except Exception as e:
            app_logger.warning(
                "87a65b58-d14e-4a41-b678-e3fcb71eff5c",
                f"Warning: {str(e)}. Retrying ({attempt + 1}/{MAX_RETRIES})",
                extra=log_fields,
            )
            exponential_backoff(attempt)

    app_logger.error(
        "2b51cd6b-2fdc-4dd2-b40f-dad9a7f59f63",
        f"{error_message}: Failed to process request after {MAX_RETRIES} retries.",
        extra=log_fields,
    )
    return (
        jsonify({"error": "Failed to process request after  {MAX_RETRIES}  retries."}),
        500,
    )

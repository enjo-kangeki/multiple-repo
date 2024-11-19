import base64
from flask import jsonify, Flask
import uuid

from get_channel_report import get_channel_report
from settings import MAX_RESULTS, TermType, MAX_RETRIES
from utils import check_valid_date, get_date_range_from_term_type, exponential_backoff
from logger import app_logger, make_log_fields

app = Flask(__name__)


def collectChannelPerformance():

    request_id = str(uuid.uuid4())
    log_fields = make_log_fields(
        request_id=request_id, func_name="collectChannelPerformance"
    )
    app_logger.info(
        "f3f2ac73-c2b4-46e8-9d03-14d5e75fefd4",
        "Start collectChannelPerformance function",
        extra=log_fields,
    )

    request_json = {
        "channel_id": "UCW47Uio6Y_pC_0No0Reak-g",
        "term": "",
        "start_date": "2024-10-30",
        "end_date": "2024-10-30",
    }

    channel_id = request_json.get("channel_id")
    term = request_json.get("term")
    start_date = request_json.get("start_date")
    end_date = request_json.get("end_date")

    if not (channel_id and (term or (start_date and end_date))):
        app_logger.error(
            "4f39b546-adf0-4517-8dc7-11631f23f2c6", "Missing required parameters."
        )
        return jsonify({"error": "Missing required parameters."}), 400

    if start_date and not check_valid_date(start_date):
        app_logger.error(
            "65bcd405-e882-45a4-822c-5e42cca49b9f",
            "Invalid start date format. Dates must be in YYYY-MM-DD.",
            extra=log_fields,
        )
        return (
            jsonify({"error": "Invalid date format. Dates must be in YYYY-MM-DD."}),
            400,
        )

    if end_date and not check_valid_date(end_date):
        app_logger.error(
            "65bcd405-e882-45a4-822c-5e42cca49b9f",
            "Invalid end date format. Dates must be in YYYY-MM-DD.",
            extra=log_fields,
        )
        return (
            jsonify({"error": "Invalid date format. Dates must be in YYYY-MM-DD."}),
            400,
        )

    if term and term in [item.value for item in TermType]:
        start_date, end_date = get_date_range_from_term_type(term)

    start_index = 1
    max_results = int(MAX_RESULTS)

    for attempt in range(MAX_RETRIES):
        try:
            get_channel_report(
                request_id, channel_id, start_index, max_results, start_date, end_date
            )
            return jsonify({"success": f"Processing {term} data"}), 200
        except Exception as e:
            app_logger.error(
                "a4a5a618-29f7-426b-8fe7-0fb11f5459fc",
                f"Error: {str(e)}. Retrying ({attempt + 1}/{MAX_RETRIES})",
            )
            exponential_backoff(attempt)

    return jsonify({"error": "Failed to process request after retries."}), 500


if __name__ == "__main__":
    with app.app_context():
        collectChannelPerformance()

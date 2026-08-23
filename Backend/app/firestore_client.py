import os
import json
import uuid
import datetime

class FirestoreClient:
    def __init__(self):
        self.db_path = "local_db.json"
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"farmers": {}, "farm_journals": {}, "farmer_connections": {}, "fields": {}}, f)

    def _read_db(self):
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"farmers": {}, "farm_journals": {}, "farmer_connections": {}, "fields": {}}

    def _write_db(self, data):
        with open(self.db_path, "w") as f:
            json.dump(data, f)

    def get_farmer(self, session_token):
        """Retrieve farmer by session token."""
        db = self._read_db()
        for fid, data in db.get('farmers', {}).items():
            if data.get('session_token') == session_token:
                data['id'] = fid
                return data
        return None

    def create_farmer(self, farmer_data):
        """Create a new farmer."""
        db = self._read_db()
        fid = str(uuid.uuid4())
        db['farmers'][fid] = farmer_data
        self._write_db(db)
        return fid

    def update_farmer(self, session_token, data_to_update):
        """Update an existing farmer's profile using their session token."""
        db = self._read_db()
        for fid, data in db.get('farmers', {}).items():
            if data.get('session_token') == session_token:
                db['farmers'][fid].update(data_to_update)
                self._write_db(db)
                return True
        return False

    def create_journal(self, journal_data):
        """Create a new farm journal entry."""
        db = self._read_db()
        jid = str(uuid.uuid4())
        db['farm_journals'][jid] = journal_data
        self._write_db(db)
        return jid

    def update_journal(self, journal_id, data):
        """Update a farm journal entry."""
        db = self._read_db()
        if journal_id in db.get('farm_journals', {}):
            db['farm_journals'][journal_id].update(data)
            self._write_db(db)

    def create_field(self, farmer_id, field_data):
        """Create a new field for a farmer."""
        db = self._read_db()
        fid = str(uuid.uuid4())
        db['fields'][fid] = field_data
        self._write_db(db)
        return fid

    def record_farmer_connection(self, seeking_farmer_id, solver_farmer_id, journal_id, via_channel):
        """Record a connection between two farmers."""
        db = self._read_db()
        cid = str(uuid.uuid4())
        db['farmer_connections'][cid] = {
            "seeker_id": seeking_farmer_id,
            "solver_id": solver_farmer_id,
            "journal_id": journal_id,
            "via_channel": via_channel,
            "connected_at": str(datetime.datetime.now())
        }
        self._write_db(db)
        return cid

    def get_past_solvers(self, issue_category, location, current_farmer_id):
        """Find farmers who solved similar issues in the same region."""
        return []

# Initialize a single global instance
firestore_client = FirestoreClient()

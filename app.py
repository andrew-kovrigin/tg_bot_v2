import os
from flask import Flask
from data.flask_config import config
from data.config import FLASK_PORT
from flask_session import Session
from flask_session.sessions import FileSystemSessionInterface
import secrets
from security import security_manager
from error_handlers import register_error_handlers
from admin_routes import admin_bp


class CustomFileSystemSessionInterface(FileSystemSessionInterface):
    """Custom session interface that ensures session IDs are always strings"""
    
    def save_session(self, app, session, response):
        """Save session with proper string handling"""
        # Check if session is empty and not modified
        if not session:
            # If the session is empty, check if we should delete the cookie
            if session.modified:
                response.delete_cookie(
                    app.config["SESSION_COOKIE_NAME"],
                    domain=self.get_cookie_domain(app),
                    path=self.get_cookie_path(app)
                )
            return
        
        # Ensure session.sid is a string before saving
        if hasattr(session, 'sid') and session.sid is not None:
            if isinstance(session.sid, bytes):
                session.sid = session.sid.decode('utf-8')
            elif not isinstance(session.sid, str):
                session.sid = str(session.sid)
        
        # Handle the session ID properly when using a signer
        if self.use_signer:
            # Get the signer
            signer = self._get_signer(app)
            if signer is not None:
                # Sign the session ID (this returns bytes)
                signed_session_id = signer.sign(session.sid.encode('utf-8') if isinstance(session.sid, str) else session.sid)
                # Convert bytes to string for cookie handling
                if isinstance(signed_session_id, bytes):
                    signed_session_id = signed_session_id.decode('utf-8')
                
                # Store the properly formatted session ID
                session_id = signed_session_id
            else:
                session_id = session.sid
        else:
            session_id = session.sid
            
            # Ensure session_id is a string for cookie handling
            if isinstance(session_id, bytes):
                session_id = session_id.decode('utf-8')
            elif not isinstance(session_id, str):
                session_id = str(session_id)
        
        # Now call the parent method but with our properly formatted session ID
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        conditional_cookie_kwargs = {}
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        if hasattr(self, "get_cookie_samesite"):
            conditional_cookie_kwargs["samesite"] = self.get_cookie_samesite(app)
        expires = self.get_expiration_time(app, session)
        data = dict(session)
        self.cache.set(self.key_prefix + session.sid, data,
                       total_seconds(app.permanent_session_lifetime))
        
        # Set the cookie with the properly formatted session ID
        response.set_cookie(app.config["SESSION_COOKIE_NAME"], session_id,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure,
                            **conditional_cookie_kwargs)


class CustomSession(Session):
    """Custom Session class that uses our custom session interface"""
    
    def _get_interface(self, app):
        """Get the appropriate session interface"""
        # For filesystem sessions, use our custom interface
        if app.config.get('SESSION_TYPE') == 'filesystem':
            # Get the parameters the original method would use
            cache_dir = app.config.get('SESSION_FILE_DIR', './flask_session')
            threshold = app.config.get('SESSION_FILE_THRESHOLD', 500)
            mode = app.config.get('SESSION_FILE_MODE', 384)
            key_prefix = app.config.get('SESSION_KEY_PREFIX', 'session:')
            use_signer = app.config.get('SESSION_USE_SIGNER', False)
            permanent = app.config.get('SESSION_PERMANENT', True)
            
            return CustomFileSystemSessionInterface(
                cache_dir, threshold, mode, key_prefix, use_signer, permanent
            )
        
        # For other session types, use the default
        return super()._get_interface(app)


def total_seconds(td):
    """Calculate total seconds in a timedelta"""
    return td.days * 24 * 60 * 60 + td.seconds


def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CustomSession(app)
    
    # Initialize security
    security_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    
    # Create session directory if it doesn't exist
    if app.config['SESSION_TYPE'] == 'filesystem':
        session_dir = app.config['SESSION_FILE_DIR']
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=FLASK_PORT)
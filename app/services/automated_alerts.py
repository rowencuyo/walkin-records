"""
Automated Alerts & Reminders system.
Manages notifications for visa expiry, missing documents, etc.
"""
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer, Signal, QObject

from app.models import WalkInRecord
from app.services.dashboard_service import DashboardService
from app.services.notification_service import NotificationService
from app.services.preferences_service import PreferencesService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AlertType:
    """Alert type constants."""
    VISA_EXPIRING_SOON = "visa_expiring_soon"
    VISA_EXPIRED = "visa_expired"
    MISSING_DOCUMENTS = "missing_documents"
    NEW_RECORD = "new_record"
    RECORD_UPDATED = "record_updated"


class AutomatedAlertsManager(QObject):
    """Manages automatic alerts and reminders for walk-in records."""
    
    alert_triggered = Signal(str, str, int)  # (alert_type, message, count)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dashboard = DashboardService()
        self._notifications = NotificationService()
        self._prefs = PreferencesService()
        
        # Check timer - runs every hour
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_alerts)
        self._check_timer.setInterval(3600000)  # 1 hour
        
        # Load settings
        self._load_settings()
    
    def start(self):
        """Start the alerts manager."""
        logger.info("Starting automated alerts manager")
        self._check_timer.start()
        # Check immediately on startup
        self._check_alerts()
    
    def stop(self):
        """Stop the alerts manager."""
        logger.info("Stopping automated alerts manager")
        self._check_timer.stop()
    
    def _load_settings(self):
        """Load alert settings from preferences."""
        self.visa_expiry_threshold = self._prefs.get_int(
            "alert_visa_expiry_days", 30
        )
        self.check_missing_docs = self._prefs.get_bool(
            "alert_missing_documents", True
        )
        self.check_visa_status = self._prefs.get_bool(
            "alert_visa_status", True
        )
        self.enable_email_digest = self._prefs.get_bool(
            "alert_email_digest", False
        )
        self.digest_time = self._prefs.get(
            "alert_digest_time", "09:00"  # 9 AM default
        )
    
    def _check_alerts(self):
        """Check for alerts that need to be triggered."""
        logger.debug("Checking for automated alerts")
        
        try:
            if self.check_visa_status:
                self._check_visa_alerts()
            
            if self.check_missing_docs:
                self._check_document_alerts()
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _check_visa_alerts(self):
        """Check for visa expiry alerts."""
        # Expired visas
        expired = self._dashboard.get_expired_visas_count()
        if expired > 0:
            notif_id = self._create_or_update_notification(
                AlertType.VISA_EXPIRED,
                f"⚠️ {expired} visa(s) expired",
                f"{expired} walk-in records have expired visas",
                severity="critical"
            )
            if notif_id:
                self.alert_triggered.emit(
                    AlertType.VISA_EXPIRED,
                    f"{expired} visa(s) expired",
                    expired
                )
        
        # Expiring soon
        expiring = self._dashboard.get_expiring_visas_count(
            days=self.visa_expiry_threshold
        )
        if expiring > 0:
            notif_id = self._create_or_update_notification(
                AlertType.VISA_EXPIRING_SOON,
                f"🔔 {expiring} visa(s) expiring in {self.visa_expiry_threshold} days",
                f"{expiring} walk-in records have visas expiring soon",
                severity="warning"
            )
            if notif_id:
                self.alert_triggered.emit(
                    AlertType.VISA_EXPIRING_SOON,
                    f"{expiring} visa(s) expiring soon",
                    expiring
                )
    
    def _check_document_alerts(self):
        """Check for missing document alerts."""
        missing = self._dashboard.get_missing_docs_count()
        if missing > 0:
            notif_id = self._create_or_update_notification(
                AlertType.MISSING_DOCUMENTS,
                f"📄 {missing} record(s) with missing documents",
                f"{missing} walk-in records have incomplete documentation",
                severity="warning"
            )
            if notif_id:
                self.alert_triggered.emit(
                    AlertType.MISSING_DOCUMENTS,
                    f"{missing} record(s) missing documents",
                    missing
                )
    
    def _create_or_update_notification(
        self,
        notif_type: str,
        title: str,
        message: str,
        severity: str = "info",
        action_type: str = "view_records"
    ) -> int | None:
        """
        Create or update a notification.
        Returns the notification ID.
        """
        try:
            # Check if notification of this type already exists
            existing = self._notifications.get_active_notifications()
            existing_notif = None
            for notif in existing:
                if getattr(notif, 'type', None) == notif_type:
                    existing_notif = notif
                    break
            
            if existing_notif:
                # Update existing notification
                logger.debug(f"Updating notification: {notif_type}")
                # TODO: Implement update method
                return getattr(existing_notif, 'id', None)
            else:
                # Create new notification
                logger.debug(f"Creating notification: {notif_type}")
                notif_id = self._notifications.create_notification(
                    title=title,
                    message=message,
                    severity=severity,
                    notif_type=notif_type,
                    action_type=action_type
                )
                return notif_id
        
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    def set_visa_expiry_threshold(self, days: int):
        """Set the visa expiry alert threshold in days."""
        self.visa_expiry_threshold = days
        self._prefs.set("alert_visa_expiry_days", days)
        logger.info(f"Visa expiry threshold set to {days} days")
    
    def set_check_missing_docs(self, enabled: bool):
        """Enable/disable missing document alerts."""
        self.check_missing_docs = enabled
        self._prefs.set("alert_missing_documents", enabled)
        logger.info(f"Missing document alerts: {'enabled' if enabled else 'disabled'}")
    
    def set_check_visa_status(self, enabled: bool):
        """Enable/disable visa status alerts."""
        self.check_visa_status = enabled
        self._prefs.set("alert_visa_status", enabled)
        logger.info(f"Visa status alerts: {'enabled' if enabled else 'disabled'}")
    
    def set_email_digest(self, enabled: bool, time: str = "09:00"):
        """Enable/disable email digest and set time."""
        self.enable_email_digest = enabled
        self.digest_time = time
        self._prefs.set("alert_email_digest", enabled)
        self._prefs.set("alert_digest_time", time)
        logger.info(f"Email digest: {'enabled' if enabled else 'disabled'} at {time}")
    
    def trigger_manual_check(self):
        """Manually trigger alert check (for testing/on-demand)."""
        logger.info("Manual alert check triggered")
        self._check_alerts()
    
    def get_alert_settings(self) -> dict:
        """Get current alert settings."""
        return {
            "visa_expiry_threshold": self.visa_expiry_threshold,
            "check_missing_docs": self.check_missing_docs,
            "check_visa_status": self.check_visa_status,
            "enable_email_digest": self.enable_email_digest,
            "digest_time": self.digest_time,
        }


class AlertScheduler:
    """Helper class for scheduling recurring alerts."""
    
    @staticmethod
    def should_send_daily_digest(last_sent: datetime | None, digest_time: str = "09:00") -> bool:
        """
        Check if daily digest should be sent.
        Returns True if it's past digest_time and no digest was sent today.
        """
        now = datetime.now()
        hour, minute = map(int, digest_time.split(":"))
        digest_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If it's before digest time today, don't send
        if now < digest_dt:
            return False
        
        # If last_sent is None, send
        if last_sent is None:
            return True
        
        # If last_sent was before today, send
        if last_sent.date() < now.date():
            return True
        
        return False
    
    @staticmethod
    def get_next_alert_time(alert_rule: dict) -> datetime:
        """
        Calculate the next alert time based on alert rule.
        
        Example rule:
        {
            "frequency": "daily",  # or "weekly", "monthly"
            "time": "09:00",
            "days": [0, 1, 2, 3, 4],  # Monday-Friday
        }
        """
        now = datetime.now()
        frequency = alert_rule.get("frequency", "daily")
        time_str = alert_rule.get("time", "09:00")
        days = alert_rule.get("days", list(range(7)))  # All days
        
        hour, minute = map(int, time_str.split(":"))
        
        if frequency == "daily":
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
        
        elif frequency == "weekly":
            # Find next occurrence on specified weekday
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            while next_time.weekday() not in days or next_time <= now:
                next_time += timedelta(days=1)
        
        else:  # monthly
            # First day of next month
            if now.month == 12:
                next_time = now.replace(year=now.year+1, month=1, day=1, hour=hour, minute=minute)
            else:
                next_time = now.replace(month=now.month+1, day=1, hour=hour, minute=minute)
        
        return next_time

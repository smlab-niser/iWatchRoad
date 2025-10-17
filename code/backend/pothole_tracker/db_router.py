class DatabaseRouter:
    """
    A router to control all database operations on models
    """

    route_app_labels = {'government'}

    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label in self.route_app_labels:
            return 'government'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label in self.route_app_labels:
            return 'government'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default', 'government'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that certain apps' models get created on the right database."""
        if app_label in self.route_app_labels:
            return db == 'government'
        elif db == 'government':
            return False
        return db == 'default'

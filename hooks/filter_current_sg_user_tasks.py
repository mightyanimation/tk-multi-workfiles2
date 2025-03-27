import sgtk

HookClass = sgtk.get_hook_baseclass()


class FilterUsers(HookClass):
    """
    Hook that can be used to retrieve a list of filtered users
    """

    def resolve_project_backend(self):
        """
        Finds the backend for the current project, taking in account project or user
        overrides

        :returns:   A tuple of (backend, host, root)
        """
        engine = self.parent.engine

        # collect available backends
        if not hasattr(self, "available_backends"):
            available_backends = engine.execute_hook_expression(
                "{config}/resolve_transfer_backend.py",
                "collect_backends"
            )

            if not available_backends:
                engine.logger.warning("Couldn't collect available backends")
                return None

            self.available_backends = available_backends

        # resolve_backend_overrides per project or per user. If no overrides are found,
        # the project location will be used
        host_backend, host_domain, host_root = engine.execute_hook_expression(
            "{config}/resolve_transfer_backend.py",
            "resolve_project_transfer_backend",
            available_backends=self.available_backends
        )

        return host_backend, host_domain, host_root

    def get_current_user_credentials(self):
        engine = self.parent.engine

        # get project transfer backend, taking in account per project or per user
        # overrides
        host_backend, host_domain, host_root = self.resolve_project_backend()

        transfer_backend = self.available_backends.get(host_backend)
        transfer_backend.set_remote_host(host_domain)
        transfer_backend.set_remote_root(host_root)

        test_credentials = transfer_backend.test_credentials

        login_framework = self.available_backends.get("login")
        if not login_framework:
            login_framework = self.load_framework("mty-framework-login")

        login = login_framework.Login(
            None, auth_callback=test_credentials, logger=self.logger
        )
        msg = "Type credentials for {0}".format(host_domain)

        credentials = login.login(host_backend.upper(), msg)
        if not credentials:
            msg = "Failed to get proper user credentials for {}".format(
                host_backend.upper()
            )
            engine.logger.error(msg)
            return None

        return credentials

    def get_current_sg_user(self):
        """Returns the sg user that matches the current transfer backend user"""
        engine = self.parent.engine

        user_credentials = self.get_current_user_credentials()
        if not user_credentials:
            engine.logger.warning("Couldn't get user credentials")
            return None

        user_name = user_credentials[0]
        if not user_name:
            engine.logger.warning("Couldn't get user name")
            return None
        engine.logger.info("User name: {}".format(user_name))

        filters = [["sg_server_username", "is", user_name]]
        fields = ["id", "type", "sg_server_username", "login"]

        sg_current_user = engine.shotgun.find_one("HumanUser", filters, fields)

        if not sg_current_user:
            engine.logger.warning(
                "Couldn't find user with sg_server_username: {}".format(user_name)
            )
            return None

        return sg_current_user

    def get_my_tasks_filters(self):
        """returns a list of filters to find the tasks assigned to the current sg user"""
        engine = self.parent.engine

        sg_current_user = self.get_current_sg_user()
        if not sg_current_user:
            engine.logger.warning("Couldn't get current sg user")
            return []

        my_tasks_filters = [
            ["project", "is", engine.context.project],
            ["sg_status_list", "not_in", ["na", "wtg", "hld", "mfwd", "sftapp", "snt", "apr", "cbb"]],
            {
                "filter_operator": "any",
                "filters": [
                    ["task_assignees", "is", sg_current_user],
                    ["sg_fixes_by", "is", sg_current_user],
                ],
            },
        ]

        return my_tasks_filters


    def find_user_assigned_tasks(self):
        """finds the tasks assigned to the current user in the current project"""
        engine = self.parent.engine

        filters = self.get_my_tasks_filters()

        fileds = [
            "id", "type", "content", "task_assignees", "sg_status_list", "sg_fixes_by"
        ]
        current_sg_user_tasks = engine.shotgun.find("Task", filters, fileds)

        if not current_sg_user_tasks:
            return None

        return current_sg_user_tasks

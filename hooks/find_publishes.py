# Copyright (c) 2022 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

HookClass = sgtk.get_hook_baseclass()


class FindPublishes(HookClass):
    """
    Hook that can be used to extend the filters list to be use to get the 
    latest publishes from ShotGrid for the Work area
    """

    def execute(self, context, filters, fields, **kwargs):
        """
        Main hook entry point

        :param context:      The context that we are searching for published files
        :param filters:      The filters that we are searching for published files
        :param fields:       The fields that we are searching for published files

        :returns:            The list of ShotGrid published files to use in app 
                             for current Work area
        """
        app = self.parent

        filters.extend(
            []
        )

        # a default order where the latest published file will always arrive first
        order = [
            {'field_name':'version_number', 'direction':'desc'}, 
            {'field_name':'created_at', 'direction':'desc'}
        ]

        # a default limit to ensure that we get all publishes
        # but that can be set to a maximum publishes to get from shotgrid
        # The "Latest N" published files
        limit = 0

        find_query_options = {
            'filters': filters,
            'fields': fields,
            'order': order,
            'limit': limit
        }

        return find_query_options

import base64
import json
import copy


def stat_widget(link, containerColums, title, subtitle, subtitle_color, stat, icon_name):
    """Return a valid format to render a Stat widget"""
    return {
        "type": "card",
        "link": link,
        "containerColumns": containerColums,
        "widgets": [
            {
                "type": "Stat",
                "data": {
                    "title": title,
                    "subtitle": subtitle,
                    "subtitleColor": subtitle_color,
                    "stat": stat,
                    "iconName": icon_name,
                },
            }
        ],
    }


def instance_widget(containerColumns, pairs, status, title, buttons):
    """Return a valid format to render an Instance widget"""
    return {
        "type": "card",
        "containerColumns": containerColumns,
        "widgets": [
            {
                "type": "Instance",
                "data": {
                    "pairs": pairs,
                    "status": status,
                    "title": title,
                    "buttons": buttons,
                },
            }
        ],
    }


def home_builder(data):
    """
    It returns the needed format from data to render the home page in JSON format for the Vue.js builder
    """
    version_card = stat_widget(
        link="https://panel.bunkerweb.io/?utm_campaign=self&utm_source=ui#pro",
        containerColums={"pc": 4, "tablet": 6, "mobile": 12},
        title="home_version",
        subtitle=(
            "home_all_features_available"
            if data.get("is_pro_version")
            else (
                "home_awaiting_compliance"
                if data.get("pro_status") == "active" and data.get("pro_overlapped")
                else (
                    "home_renew_license"
                    if data.get("pro_status") == "expired"
                    else "home_talk_to_team" if data.get("pro_status") == "suspended" else "home_upgrade_to_pro"
                )
            )
        ),
        subtitle_color="success" if data.get("is_pro_version") else "warning",
        stat=(
            "home_pro"
            if data.get("is_pro_version")
            else (
                "home_pro_locked"
                if data.get("pro_status") == "active" and data.get("pro_overlapped")
                else "home_expired" if data.get("pro_status") == "expired" else "home_suspended" if data.get("pro_status") == "suspended" else "home_free"
            )
        ),
        icon_name="crown" if data.get("is_pro_version") else "key",
    )

    version_num_card = stat_widget(
        link="https://github.com/bunkerity/bunkerweb",
        containerColums={"pc": 4, "tablet": 6, "mobile": 12},
        title="home_version_number",
        subtitle=(
            "home_couldnt_find_remote"
            if not data.get("remote_version")
            else "home_latest_version" if data.get("remote_version") and data.get("check_version") else "home_update_available"
        ),
        subtitle_color=("error" if not data.get("remote_version") else "success" if data.get("remote_version") and data.get("check_version") else "warning"),
        stat=data.get("version"),
        icon_name="wire",
    )

    instances_card = stat_widget(
        link="instances",
        containerColums={"pc": 4, "tablet": 6, "mobile": 12},
        title="home_instances",
        subtitle="home_total_number",
        subtitle_color="info",
        stat=data.get("instances_number"),
        icon_name="box",
    )

    services_card = stat_widget(
        link="services",
        containerColums={"pc": 4, "tablet": 6, "mobile": 12},
        title="home_services",
        subtitle="home_all_methods_included",
        subtitle_color="info",
        stat=data.get("services_number"),
        icon_name="disk",
    )

    plugins_card = stat_widget(
        link="plugins",
        containerColums={"pc": 4, "tablet": 6, "mobile": 12},
        title="home_plugins",
        subtitle="home_errors_found" if data.get("plugins_errors") > 0 else "home_no_error",
        subtitle_color="error" if data.get("plugins_errors") > 0 else "success",
        stat=data.get("plugins_number"),
        icon_name="puzzle",
    )

    builder = [version_card, version_num_card, instances_card, services_card, plugins_card]

    return base64.b64encode(bytes(json.dumps(builder), "utf-8")).decode("ascii")


def instances_builder(instances: list):
    """
    It returns the needed format from data to render the instances page in JSON format for the Vue.js builder
    """
    builder = []

    for instance in instances:
        # setup actions buttons
        actions = (
            ["restart", "stop"]
            if instance._type == "local" and instance.health
            else (
                ["reload", "stop"]
                if not instance._type == "local" and instance.health
                else ["start"] if instance._type == "local" and not instance.health else []
            )
        )

        buttons = [
            {
                "attrs": {
                    "data-submit-form": f"""{{"INSTANCE_ID" : "{instance._id}", "operation" : "{action}" }}""",
                },
                "text": f"action_{action}",
                "color": "success" if action == "start" else "error" if action == "stop" else "warning",
            }
            for action in actions
        ]

        instance = instance_widget(
            containerColumns={"pc": 6, "tablet": 6, "mobile": 12},
            pairs=[
                {"key": "instances_hostname", "value": instance.hostname},
                {"key": "instances_type", "value": instance._type},
                {"key": "instances_status", "value": "instances_active" if instance.health else "instances_inactive"},
            ],
            status="success" if instance.health else "error",
            title=instance.name,
            buttons=buttons,
        )

        builder.append(instance)

    return base64.b64encode(bytes(json.dumps(builder), "utf-8")).decode("ascii")


def get_forms(templates=[], plugins=[], settings={}):
    """
    Will generate every needed form using templates, plugins and settings.
    We will run on each plugins, set template value if one, and override by the custom settings value if exists.
    We will format to fit each form type (easy, advanced, raw).
    """
    forms = {"advanced": {}, "easy": {}, "raw": {}}

    for template in templates:
        forms["advanced"][template.get("name")] = set_advanced(template, plugins, settings)
        forms["raw"][template.get("name")] = set_raw(template, plugins, settings)
        forms["easy"][template.get("name")] = set_easy(template, plugins, settings)

    return forms


def set_easy(template, plugins_base, settings):
    """
    Prepare the easy form based on the template and plugins data.
    We need to loop on each steps and prepare settings and configs for each step.
    """
    template_settings = template.get("settings")
    plugins = copy.deepcopy(plugins_base)
    steps = template.get("steps")

    for step in steps:
        step_settings = step.get("settings", {})
        # Loop on step settings to set the settings value
        loop_id = 0
        step_settings_output = {}
        for setting in step_settings:
            loop_id += 1
            # Get relate setting from plugins using setting name
            plugin = next(
                (plugin for plugin in plugins if setting in plugin.get("settings")),
                None,
            )

            if not plugin:
                continue

            if not plugin.get("settings").get(setting):
                continue

            plugin_setting = copy.deepcopy(plugin.get("settings").get(setting))

            plugin_setting = format_setting(
                setting,
                plugin_setting,
                len(step_settings),
                loop_id,
                template_settings,
                settings,
            )

            step_settings_output[setting] = plugin_setting

        step["settings"] = step_settings_output

    return steps


def set_raw(template, plugins_base, settings):
    """
    Set the raw form based on the template and plugins data.
    It consists of keeping only the value or default value for each plugin settings.
    """
    template_settings = template.get("settings")
    raw_settings = {}
    # Copy of the plugins base
    plugins = copy.deepcopy(plugins_base)
    # Update settings with global config data
    for plugin in plugins:
        for setting, value in plugin.get("settings").items():
            # avoid some methods from services_settings
            if setting in settings and settings[setting].get("method", "ui") not in ("ui", "default", "manual"):
                continue

            raw_value = None

            # Start by setting template value if exists
            if setting in template_settings:
                # Update value or set default as value
                raw_value = template_settings.get(setting, value.get("default"))

            # Then override by service settings
            if setting in settings:
                raw_value = settings[setting].get("value", value.get("value", value.get("default")))

            # Add value only if exists
            if raw_value:
                raw_settings[setting] = raw_value

    return raw_settings


def set_advanced(template, plugins_base, settings):
    """
    Set the advanced form based on the template and plugins data.
    It consists of formatting each plugin settings to be used in the advanced form.
    """
    template_settings = template.get("settings")
    # Copy of the plugins base data
    plugins = copy.deepcopy(plugins_base)
    # Update settings with global config data
    for plugin in plugins:
        loop_id = 0
        total_settings = len(plugin.get("settings"))
        for setting, value in plugin.get("settings").items():
            loop_id += 1
            value = format_setting(
                setting,
                value,
                total_settings,
                loop_id,
                template_settings,
                settings,
            )

    set_multiples(template, plugins, settings)

    return plugins


def get_multiple_from_template(template, multiples):
    """
    We are gonna loop on each plugins multiples group, in case a setting is matching a template setting,
    we will create a group using the prefix as key (or "0" if no prefix) with default settings at first.
    Then we will override by the template value in case there is one.
    This will return something of this type :
    {'0' : {'setting' : value, 'setting2': value2}, '1' : {'setting_1': value, 'setting2_1': value}} }
    """
    # Loop on each plugin and loop on multiples key
    # Check if the name us matching a template key
    multiple_plugin = copy.deepcopy(multiples)

    multiple_template = {}
    for setting, value in template.get("settings").items():
        # Sanitize setting name to remove prefix of type _1 if exists
        # Slipt by _ and check if last element is a digit
        format_setting = setting
        setting_split = setting.split("_")
        prefix = "0"
        if setting_split[-1].isdigit():
            prefix = setting_split[-1]
            format_setting = "_".join(setting_split[:-1])
        # loop on settings of a multiple group
        for mult_name, mult_settings in multiple_plugin.items():
            # Check if at least one multiple plugin setting is matching the template setting
            if format_setting in mult_settings:
                if not mult_name in multiple_template:
                    multiple_template[mult_name] = {}
                # Case it is, we will check if already a group with the right prefix exists
                # If not, we will create it
                if not prefix in multiple_template[mult_name]:
                    # We want each settings to have the prefix if exists
                    # We will get the value of the setting without the prefix and create a prefix key with the same value
                    # And after that we can delete the original setting
                    new_multiple_group = {}
                    for multSett, multValue in mult_settings.items():
                        new_multiple_group[f"{multSett}{f'_{prefix}' if prefix != '0' else ''}"] = multValue

                    new_multiple_group = copy.deepcopy(new_multiple_group)

                    # Update id for each settings
                    for multSett, multValue in new_multiple_group.items():
                        multValue["id"] = f"{multValue['id']}{f'-{prefix}' if prefix != '0' else ''}"

                    multiple_template[mult_name][prefix] = new_multiple_group

                # We can now add the template value to setting using the same setting name with prefix
                multiple_template[mult_name][prefix][setting]["value"] = value

                # Sort key incrementally
                for mult_name, mult_settings in multiple_template.items():
                    multiple_template[mult_name] = dict(sorted(mult_settings.items(), key=lambda item: int(item[0])))
    return multiple_template


def get_multiple_from_settings(settings, multiples):
    """
    We are gonna loop on each plugins multiples group, in case a setting is matching a service / global config setting,
    we will create a group using the prefix as key (or "0" if no prefix) with default settings at first.
    Then we will override by the service / global config value in case there is one.
    This will return something of this type :
    {'0' : {'setting' : value, 'setting2': value2}, '1' : {'setting_1': value, 'setting2_1': value}} }
    """

    # Loop on each plugin and loop on multiples key
    # Check if the name us matching a template key
    multiple_plugins = copy.deepcopy(multiples)

    multiple_settings = {}
    for setting, value in settings.items():
        # Sanitize setting name to remove prefix of type _1 if exists
        # Slipt by _ and check if last element is a digit
        format_setting = setting
        setting_split = setting.split("_")
        prefix = "0"
        if setting_split[-1].isdigit():
            prefix = setting_split[-1]
            format_setting = "_".join(setting_split[:-1])
        # loop on settings of a multiple group
        for mult_name, mult_settings in multiple_plugins.items():
            # Check if at least one multiple plugin setting is matching the template setting
            if format_setting in mult_settings:

                if not mult_name in multiple_settings:
                    multiple_settings[mult_name] = {}
                # Case it is, we will check if already a group with the right prefix exists
                # If not, we will create it
                if not prefix in multiple_settings:
                    # We want each settings to have the prefix if exists
                    # We will get the value of the setting without the prefix and create a prefix key with the same value
                    # And after that we can delete the original setting
                    new_multiple_group = {}
                    for multSett, multValue in mult_settings.items():
                        new_multiple_group[f"{multSett}{f'_{prefix}' if prefix != '0' else ''}"] = multValue

                    new_multiple_group = copy.deepcopy(new_multiple_group)

                    # Update id for each settings
                    for multSett, multValue in new_multiple_group.items():
                        multValue["id"] = f"{multValue['id']}{f'-{prefix}' if prefix != '0' else ''}"

                    multiple_settings[mult_name][prefix] = new_multiple_group

                # We can now add the template value to setting using the same setting name with prefix
                multiple_settings[mult_name][prefix][setting]["value"] = value.get("value", multiple_settings[mult_name][prefix][setting]["value"])
                multiple_settings[mult_name][prefix][setting]["method"] = value.get("method", "ui")
                multiple_settings[mult_name][prefix][setting]["disabled"] = False if value.get("method", "ui") in ("ui", "default", "manual") else True
                if multiple_settings[mult_name][prefix][setting].get("disabled", False):
                    multiple_settings[mult_name][prefix][setting]["popovers"] = [
                        {
                            "iconName": "trespass",
                            "text": "inp_popover_method_disabled",
                        }
                    ] + multiple_settings[mult_name][prefix][setting].get("popovers", [])
    return multiple_settings


def set_multiples(template, format_plugins, service_settings):
    """
    Set the multiples settings for each plugin.
    """
    # copy of format plugins
    for plugin in format_plugins:
        # Get multiples
        multiples = {}
        settings_to_delete = []
        total_settings = len(plugin.get("settings"))
        zindex = 0
        for setting, value in plugin.get("settings").items():

            if not value.get("multiple"):
                continue

            zindex += 1

            value["containerClass"] = f"z-{total_settings - zindex}"

            mult_name = value.get("multiple")
            # Get the multiple value and set it as key if not in multiples dict
            if mult_name not in multiples:
                multiples[mult_name] = {}

            multiples[mult_name][setting] = value
            settings_to_delete.append(setting)

        # Delete multiple settings from regular settings
        for setting in settings_to_delete:
            del plugin["settings"][setting]

        if len(multiples):
            # Add multiple schema with default values to plugin
            plugin["multiples_schema"] = multiples
            # Now that we have for each plugin the multiples settings, we need to do the following
            # Get all settings from template that are multiples
            template_multiples = get_multiple_from_template(template, multiples)
            # Get all settings from service settings / global config that are multiples
            service_multiples = get_multiple_from_settings(service_settings, multiples)
            # Get service multiples if at least one, else use template multiples
            plugin["multiples"] = service_multiples if len(service_multiples) else template_multiples

    return format_plugins


def format_setting(
    setting_name,
    setting_value,
    total_settings,
    loop_id,
    template_settings,
    service_settings,
):
    """
    Format a setting in order to be used with form builder.
    This will only set value for none multiple settings.
    Additionnel set_multiples function will handle multiple settings.
    """
    # add zindex for field in case not a multiple
    # Case multiple, this will be set on the group level
    if not "multiple" in setting_value:
        setting_value["containerClass"] = f"z-{total_settings - loop_id}"

    # regex by pattern
    setting_value["pattern"] = setting_value.get("regex", "")

    # set inpType based on type define for each settings
    inpType = (
        "checkbox"
        if setting_value.get("type") == "check"
        else ("select" if setting_value.get("type") == "select" else "datepicker" if setting_value.get("type") == "date" else "input")
    )
    setting_value["inpType"] = inpType

    # set name using the label
    setting_value["name"] = setting_value.get("label")

    # case select
    if inpType == "select":
        # replace "select" key by "values"
        setting_value["values"] = setting_value.pop("select")

    # add columns
    setting_value["columns"] = {"pc": 4, "tablet": 6, "mobile": 12}

    # By default, the input is enabled unless specific method
    setting_value["disabled"] = False

    setting_value["value"] = setting_value.get("default")

    # Start by setting template value if exists
    if setting_name in template_settings and not "multiple" in setting_value:
        # Update value or set default as value
        setting_value["value"] = template_settings.get(setting_name, setting_value.get("default"))

    # Then override by service settings if not a multiple
    # Case multiple, we need to keep the default value and override only each multiple group
    if setting_name in service_settings and not "multiple" in setting_value:
        setting_value["value"] = service_settings[setting_name].get("value", setting_value.get("value", setting_value.get("default")))
        setting_value["method"] = service_settings[setting_name].get("method", "ui")

    # Then override by service settings
    if setting_name in service_settings:
        setting_value["disabled"] = False if service_settings[setting_name].get("method", "ui") in ("ui", "default", "manual") else True

    # Prepare popover checking "help", "context"
    popovers = []

    if (setting_value.get("disabled", False)) and service_settings[setting_name].get("method", "ui") not in ("ui", "default", "manual"):
        popovers.append(
            {
                "iconName": "trespass",
                "text": "inp_popover_method_disabled",
            }
        )

    if setting_value.get("context"):
        popovers.append(
            {
                "iconName": ("disk" if setting_value.get("context") == "multisite" else "globe"),
                "text": ("inp_popover_multisite" if setting_value.get("context") == "multisite" else "inp_popover_global"),
            }
        )

    if setting_value.get("help"):
        popovers.append(
            {
                "iconName": "info",
                "text": setting_value.get("help"),
            }
        )

    setting_value["popovers"] = popovers
    return setting_value


def global_config_builder(plugins, settings):
    """Render forms with global config data.
    ATM we don't need templates but we need to pass at least one to the function (it will simply not override anything).
    """

    templates = [
        {
            "name": "default",
            "steps": [],
            "configs": {},
            "settings": {},
        }
    ]

    builder = [
        {
            "type": "card",
            "containerColumns": {"pc": 12, "tablet": 12, "mobile": 12},
            "widgets": [
                {
                    "type": "Title",
                    "data": {"title": "global_config_title", "type": "container"},
                },
                {
                    "type": "Subtitle",
                    "data": {"subtitle": "global_config_subtitle", "type": "container"},
                },
                {
                    "type": "Templates",
                    "data": {
                        "templates": get_forms(templates, plugins, settings),
                    },
                },
            ],
        }
    ]

    return base64.b64encode(bytes(json.dumps(builder), "utf-8")).decode("ascii")

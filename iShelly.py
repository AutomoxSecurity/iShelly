#!/usr/bin/python3
import sys
import os
from pick import pick
from src.modules import modules, common
import json


def main():
    global logger

    parser = common.get_parser()
    args = parser.parse_args()
    logger = common.get_logger(args)

    if not common.prereqs_present():
        sys.exit()

    os.makedirs("./Payloads/", exist_ok=True)
    all_options = common.get_options()

    logger.debug("Generating: {}".format(all_options['procedure']))
    c2 = common.C2(all_options)
    agent = common.Agent(c2, all_options)

    c2.get_payload()
    if all_options['needs-compilation']:
        c2.extract_zip()
        agent.build_operator_agent_config()
        agent.save_c2_profile_settings()
        agent.build_agent(all_options)
    agent.upload_payload()

    module = common.ModuleGenerator(agent)
    if all_options['procedure'] == 'Installer Package w/ only preinstall script':
        modules.install_pkg(module)
    elif all_options['procedure'] == 'Installer Package w/ only postinstall script':
        modules.install_pkg_postinstall(module)       
    elif all_options['procedure'] == 'Installer Package w/ Launch Daemon for Persistence':
        modules.install_pkg_ld(module)
    elif all_options['procedure'] == 'Installer Package w/ Installer Plugin':
        modules.install_pkg_installer_plugin(module)
    elif all_options['procedure'] == 'Installer Package w/ JavaScript Functionality embedded':
        modules.install_pkg_js_embedded(module)
    elif all_options['procedure'] == 'Installer Package w/ JavaScript Functionality in Script':
        modules.install_pkg_js_script(module)
    elif all_options['procedure'] == 'Disk Image':
        modules.disk_image(module)
    elif all_options['procedure'] == 'Macro VBA Excel':
        modules.macro_vba_excel(module)
    elif all_options['procedure'] == 'Macro VBA PowerPoint':
        modules.macro_vba_ppt(module)
    elif all_options['procedure'] == 'Macro VBA Word':
        modules.macro_vba_word(module)
    elif all_options['procedure'] == 'Macro SYLK Excel':
        modules.macro_sylk_excel(module)

    print(
        '\n[*] Done generating package! Navigate to ./Payloads for payload.\n')
    if not args.debug:
        logger.debug(
            'Cleaning payload staging directory.')
        module.clean_payload_staging()


if __name__ == '__main__':
    main()

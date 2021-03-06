# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.

from datetime import datetime
import os
from flask import current_app, json
from ..decorators import lazy_property
from ..extensions import db

from .state import (project_state_get, project_state_save, walkWithoutGit)


class Project(db.Model):
    __tablename__ = 'project'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(60), index=True)
    name = db.Column(db.String(60), index=True)
    full_name = db.Column(db.String(60))
    html_url = db.Column(db.String(60))
    data = db.Column(db.PickleType())
    clone = db.Column(db.String(400))
    is_github = db.Column(db.Boolean(), index=True)
    is_ready = db.Column(db.Boolean(), index=True, default=False)

    builds = db.relationship('ProjectBuild', backref='project', lazy='dynamic')

    def cache_update(self, data):
        self.html_url = data['html_url']
        self.name = data['name']
        self.data = data

    @lazy_property
    def config(self):
        # if it is not purely visible, but @lazy_property decorator cache state
        # values in runtime, when this class property acessed for the 1st time
        # it store state value. You can access it and modify, but at the end of
        # the request all modifications dies if wasn't saved
        #
        _state, _local = project_state_get(project = self)
        return {'state': _state, 'local': _local}

    def save_state(self):
        project_state_save(self)

    def setup_status(self):
        # Return project status.
        return self.config['local'].get('source', None)

    @property
    def title(self):
        """
        Return project title, resolved from repo clone if no rename family name given
        """
        # Split the git clone URL on /, take the last part, remove '.git' if it exists
        # eg "https://github.com/davelab6/league-gothic.git" -> league-gothic.git -> league-gothic
        title = self.clone.split('/')[-1].replace('.git', '')
        # If URL terminates with a /, title will be None, so take the 2nd to last part
        # eg "https://github.com/davelab6/league-gothic/" -> league-gothic
        if not title:
            title = self.clone.split('/')[-2].replace('.git', '')
        # use the family rename input if it was given
        if self.is_ready and self.config['state'].get('familyname', None):
            title = self.config['state']['familyname']
        return title

    def asset_by_name(self, name):
        """
        Resolve asset id into its real path. For internal use.

        :param name: handle for file conventionally found in repositories

        """
        DATA_ROOT = current_app.config.get('DATA_ROOT')
        if name == 'log':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.process.log' % self)
        elif name == 'yaml':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.bakery.yaml' % self)
        elif name == 'metadata':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.out/' % self, 'METADATA.json')
        elif name == 'metadata_new':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.out/' % self, 'METADATA.json.new')
        elif name == 'license':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.in/' % self, self.config['state']['license_file'])
        elif name == 'description':
            fn = os.path.join(DATA_ROOT, '%(login)s/%(id)s.out/' % self, 'DESCRIPTION.en_us.html')
        else:
            fn = None
        return fn

    def read_asset(self, name = None):
        fn = self.asset_by_name(name)
        if os.path.exists(fn) and os.path.isfile(fn):
            return unicode(open(fn, 'r').read(), "utf8")
        else:
            return ''

    def treeFromFilesystem(self, folder=None):
        """
        Read files tree in specied directory

        :param folder: handle for tree, either 'in' or 'out'

        Returns:
            folderContents: Dictionary of file and directory strings
        """
        DATA_ROOT = current_app.config.get('DATA_ROOT')
        _in = os.path.join(DATA_ROOT, '%(login)s/%(id)s.in/' % self)
        _out = os.path.join(DATA_ROOT, '%(login)s/%(id)s.out/' % self)
        if folder == 'in' and os.path.exists(_in):
            folderContents = walkWithoutGit(_in)
        elif folder == 'out' and os.path.exists(_out):
            folderContents = walkWithoutGit(_out)
        else:
            folderContents = { 'Sorry, filesystem unavailable': '' }
        return folderContents

    def textFiles(self):
        """
        Read all the text files found in the _in repo

        Returns:
            textFiles: Dictionary of file and directory strings
        """
        DATA_ROOT = current_app.config.get('DATA_ROOT')
        _in = os.path.join(DATA_ROOT, '%(login)s/%(id)s.in/' % self)
        textFiles = {}
        for textFile in self.config['local']['txt_files']:
            fn = os.path.join(_in, textFile)
            if os.path.exists(fn) and os.path.isfile(fn):
                textFiles[textFile] = unicode(open(fn, 'r').read(), "utf8")
        return textFiles

    def save_asset(self, name = None, data = None, **kwarg):
        """ Save static files into out folder """
        if name == 'description':
            f = open(self.asset_by_name(name), 'w')
            f.write(data)
            f.close()
        elif name == 'metadata':
            f = open(self.asset_by_name(name), 'w')
            json.dump(json.loads(data), f, indent=2, ensure_ascii=True) # same params as in generatemetadata.py
            f.close()

            if kwarg.get('del_new') and kwarg['del_new']:
                if os.path.exists(self.asset_by_name('metadata_new')):
                    os.remove(self.asset_by_name('metadata_new'))

    @property
    def family_stat(self):
        from ..models import FontStats

        if self.config['state'].get('stats_family_name'):
            return FontStats.by_family(self.config['state']['stats_family_name'])
        elif self.config['state'].get('familyname'):
            return FontStats.by_family(self.config['state']['familyname'])
        else:
            return None

    def __getitem__(self, key):
        """ Magic method that allow to access ORM properties using
        object-dot-propertyname """
        # make magic mapping works
        return self.__dict__.get(key)

class ProjectBuild(db.Model):
    __tablename__ = 'project_build'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    githash = db.Column(db.String(40))
    is_success = db.Column(db.Boolean())
    created = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def make_build(project_id):
        pass


class ProjectTest(db.Model):
    __tablename__ = 'project_test'
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    build_id = db.Column(db.Integer, db.ForeignKey('project.id'))


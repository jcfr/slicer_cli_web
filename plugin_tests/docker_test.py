#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import threading
import six
import types
import json

from tests import base
from girder import events
from docker import Client

# boiler plate to start and stop the server
TIMEOUT = 180
JobStatus = None

def setUpModule():
    base.enabledPlugins.extend(['jobs', 'slicer_cli'])
    base.startServer()
    JobStatus = __import__('girder.plugins.jobs.constants.JobStatus')

def tearDownModule():
    base.stopServer()


class DockerImageManagementTest(base.TestCase):

    def setUp(self):

        # adding and removing docker images and using generated rest endpoints
        # requires admin access
        base.TestCase.setUp(self)
        admin = {
            'email': 'admin@email.com',
            'login': 'adminlogin',
            'firstName': 'Admin',
            'lastName': 'Last',
            'password': 'adminpassword',
            'admin': True
        }
        self.admin = self.model('user').createUser(**admin)

        try:
            self.docker_client = Client(base_url='unix://var/run/docker.sock')
        except Exception as err:
            self.fail('could not create the docker client ' + str(err))

    def testAddNonExistentImage(self):
        # add a bad image
        img_name = 'null/null:null'
        self.assertNoImages()
        self.addImage(img_name, self.JobStatus.ERROR)
        self.assertNoImages()

    def testDockerAdd(self):
        # try to cache a good image to the mongo database
        img_name = "dsarchive/histomicstk:v0.1.3"
        self.assertNoImages()
        self.addImage(img_name, self.JobStatus.SUCCESS)
        self.imageIsLoaded(img_name, True)

    def testDockerDelete(self):
        # just delete the meta data in the mongo database
        # dont attempt to delete the docker image
        img_name = "dsarchive/histomicstk:v0.1.3"
        self.assertNoImages()
        self.addImage(img_name, self.JobStatus.SUCCESS)
        self.imageIsLoaded(img_name, True)
        self.deleteImage(img_name, True, False)
        self.imageIsLoaded(img_name, exists=False)
        self.assertNoImages()

    def testDockerDeleteFull(self):
        # attempt to delete docker image metadata and the image off the local
        # machine
        img_name = "dsarchive/histomicstk:v0.1.3"
        self.assertNoImages()
        self.addImage(img_name, self.JobStatus.SUCCESS)
        self.imageIsLoaded(img_name, True)
        self.deleteImage(img_name, True, True, self.JobStatus.SUCCESS)

        try:
            self.docker_client.inspect_image(img_name)
            self.fail('If the image was deleted then an attempt to docker '
                      'inspect it should raise a docker exception')
        except Exception:
            pass

        self.imageIsLoaded(img_name, exists=False)
        self.assertNoImages()

    def testDockerPull(self):

        # test an instance when the image must be pulled
        # Forces the test image to be deleted
        self.testDockerDeleteFull()
        self.testDockerAdd()

    def testBadImageDelete(self):
        # attempt to delete a non existent image
        img_name = 'null/null:null'
        self.assertNoImages()
        self.deleteImage(img_name, False, )

    def testXmlEndpoint(self):
        # loads an image and attempts to run an arbitrary xml endpoint

        img_name = "dsarchive/histomicstk:v0.1.3"
        self.testDockerAdd()

        name, tag = self.splitName(img_name)
        data = self.getEndpoint()
        for (image, tag) in six.iteritems(data):
            for (version_name, cli) in six.iteritems(tag):
                for (cli_name, info) in six.iteritems(cli):
                    route = info['xmlspec']
                    resp = self.request(
                        path=route,
                        user=self.admin)
                    self.assertStatus(resp, 200)
                    xmlString = self.getBody(resp)
                    # TODO validate with xml schema
                    self.assertNotEqual(xmlString, '')

    def testEndpointDeletion(self):

        img_name = "dsarchive/histomicstk:v0.1.3"
        self.testXmlEndpoint()
        data = self.getEndpoint()
        self.deleteImage(img_name, True)
        name, tag = self.splitName(img_name)

        for (image, tag) in six.iteritems(data):
            for (version_name, cli) in six.iteritems(tag):
                for (cli_name, info) in six.iteritems(cli):
                    route = info['xmlspec']
                    resp = self.request(
                        path=route,
                        user=self.admin)
                    # xml route should have been deleted
                    self.assertStatus(resp, 400)

    def testAddBadImage(self):
        # job should fail gracefully after pulling the image
        img_name = 'library/hello-world:latest'
        self.assertNoImages()
        self.addImage(img_name, self.JobStatus.ERROR)
        self.assertNoImages()

    def splitName(self, name):
        if ':' in name:
            imageAndTag = name.split(':')
        else:
            imageAndTag = name.split('@')
        return imageAndTag[0], imageAndTag[1]

    def imageIsLoaded(self, name, exists):

        userAndRepo, tag = self.splitName(name)

        data = self.getEndpoint()
        if not exists:
            if userAndRepo in data:
                imgVersions = data[userAndRepo]
                self.assertNotHasKeys(imgVersions, [tag])

        else:
            self.assertHasKeys(data, [userAndRepo])
            imgVersions = data[userAndRepo]
            self.assertHasKeys(imgVersions, [tag])

    def getEndpoint(self):

        resp = self.request(path='/slicer_cli/slicer_cli/docker_image',
                            user=self.admin)
        self.assertStatus(resp, 200)
        return json.loads(self.getBody(resp))

    def assertNoImages(self):
        data = self.getEndpoint()
        self.assertEqual({}, data,
                         " There should be no pre existing docker images ")

    def deleteImage(self, name,  responseCodeOK, deleteDockerImage=False,
                    status=4):
        """
        delete docker image data and test whether a docker
        image can be deleted off the local machine
        """
        job_status = [self.JobStatus.SUCCESS]
        if deleteDockerImage:
            event = threading.Event()

            def tempListener(self, girderEvent):
                job = girderEvent.info

                if job['type'] == 'slicer_cli_job' and \
                        (job['status'] == self.JobStatus.SUCCESS or
                         job['status'] == self.JobStatus.ERROR):

                    events.unbind('model.job.save.after', 'slicer_cli_del')
                    job_status[0] = job['status']
                    event.set()

            self.delHandler = types.MethodType(tempListener, self)

            events.bind('model.job.save.after', 'slicer_cli_del',
                        self.delHandler)

        resp = self.request(path='/slicer_cli/slicer_cli/docker_image',
                            user=self.admin, method='DELETE',
                            params={"name": json.dumps(name),
                                    "delete_from_local_repo":
                                        deleteDockerImage
                                    }, isJson=False)
        if responseCodeOK:
            self.assertStatus(resp, 200)
        else:
            try:
                self.assertStatus(resp, 200)
                self.fail('A status ok or code 200 should not have been '
                          'recieved for deleting the image %s' % str(name))
            except Exception:
                    pass
        if deleteDockerImage:
            if not event.wait(TIMEOUT):
                del self.delHandler
                self.fail('deleting the docker image is taking '
                          'longer than %d seconds' % TIMEOUT)
            else:
                del self.delHandler
                self.assertEqual(job_status[0], status,
                                 "The status of the job should "
                                 "match ")

    def addImage(self, name, status):
        """test the put endpoint, name can be a string or a list of strings"""

        event = threading.Event()
        job_status = [self.JobStatus.SUCCESS]

        def tempListener(self, girderEvent):

            job = girderEvent.info

            if (job['type'] == 'slicer_cli_job') and \
                    (job['status'] == self.JobStatus.SUCCESS or
                     job['status'] == self.JobStatus.ERROR):

                job_status[0] = job['status']

                events.unbind('model.job.save.after', 'slicer_cli_add')

                event.set()

        self.addHandler = types.MethodType(tempListener, self)

        events.bind('model.job.save.after', 'slicer_cli_add', self.addHandler)

        resp = self.request(path='/slicer_cli/slicer_cli/docker_image',
                            user=self.admin, method='PUT',
                            params={"name": json.dumps(name)}, isJson=False)

        self.assertStatus(resp, 200)

        if not event.wait(TIMEOUT):
            del self.addHandler
            self.fail('adding the docker image is taking '
                      'longer than %d seconds' % TIMEOUT)
        else:
            del self.addHandler
            self.assertEqual(job_status[0], status,
                             "The status of the job should "
                             "match ")

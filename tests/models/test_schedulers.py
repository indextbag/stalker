# -*- coding: utf-8 -*-
# Stalker a Production Asset Management System
# Copyright (C) 2009-2013 Erkan Ozgur Yilmaz
# 
# This file is part of Stalker.
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA



import unittest
import datetime
import os
from zope.sqlalchemy import ZopeTransactionExtension
from stalker import db, Department, User, Project, Repository, Status, StatusList, Task
import stalker
from stalker.db import DBSession
from stalker.models.schedulers import TaskJugglerScheduler



class TaskJugglerSchedulerTester(unittest.TestCase):
    """tests the stalker.models.scheduler.TaskJugglerScheduler class
    """
    
    @classmethod
    def setUpClass(cls):
        if DBSession:
            DBSession.remove()
        DBSession.configure(extension=None)
    
    @classmethod
    def tearDownClass(cls):
        """clean up the test
        """
        DBSession.configure(extension=ZopeTransactionExtension())
    
    def setUp(self):
        """set up the test
        """
        # we need a database
        db.setup({
            'sqlalchemy.url': 'sqlite:///:memory:',
            'sqlalchemy.echo': False
        })
        
        # replace datetime now function
        
        # create departments
        self.test_dep1 = Department(name='Dep1')
        self.test_dep2 = Department(name='Dep2')
        
        # create resources
        self.test_user1 = User(
            login='user1',
            name='User1',
            email='user1@users.com',
            password='1234',
            departments=[self.test_dep1]
        )
        DBSession.add(self.test_user1)
        
        self.test_user2 = User(
            login='user2',
            name='User2',
            email='user2@users.com',
            password='1234',
            departments=[self.test_dep1]
        )
        DBSession.add(self.test_user2)
        
        self.test_user3 = User(
            login='user3',
            name='User3',
            email='user3@users.com',
            password='1234',
            departments=[self.test_dep2]
        )
        DBSession.add(self.test_user3)
        
        self.test_user4 = User(
            login='user4',
            name='User4',
            email='user4@users.com',
            password='1234',
            departments=[self.test_dep2]
        )
        DBSession.add(self.test_user4)
        
        # user with two departments
        self.test_user5 = User(
            login='user5',
            name='User5',
            email='user5@users.com',
            password='1234',
            departments=[self.test_dep1, self.test_dep2]
        )
        DBSession.add(self.test_user5)
        
        # user with no departments
        self.test_user6 = User(
            login='user6',
            name='User6',
            email='user6@users.com',
            password='1234'
        )
        DBSession.add(self.test_user6)
        
        # repository
        self.test_repo = Repository(
            name='Test Repository',
            linux_path='/mnt/T/',
            windows_path='T:/',
            osx_path='/Volumes/T/'
        )
        DBSession.add(self.test_repo)
        
        # statuses
        self.test_status1 = Status(name='Status 1', code='STS1')
        self.test_status2 = Status(name='Status 2', code='STS2')
        self.test_status3 = Status(name='Status 3', code='STS3')
        self.test_status4 = Status(name='Status 4', code='STS4')
        self.test_status5 = Status(name='Status 5', code='STS5')
        DBSession.add_all([self.test_status1,
                           self.test_status2,
                           self.test_status3,
                           self.test_status4,
                           self.test_status5])
        
        # status lists
        self.test_proj_status_list = StatusList(
            name='Project Status List',
            statuses=[self.test_status1, self.test_status2, self.test_status3],
            target_entity_type='Project'
        )
        DBSession.add(self.test_proj_status_list) 
        
        # create one project
        self.test_proj1 = Project(
            name='Test Project 1',
            code='TP1',
            repository=self.test_repo,
            status_list=self.test_proj_status_list,
            start=datetime.datetime(2013, 4, 4),
            end = datetime.datetime(2013, 5, 4)
        )
        DBSession.add(self.test_proj1)
        self.test_proj1.now = datetime.datetime(2013, 4, 4)
        
        # create task status list
        self.test_task_status_list = StatusList(
            name='Task Statuses',
            statuses=[self.test_status4, self.test_status5],
            target_entity_type='Task'
        )
        DBSession.add(self.test_task_status_list)
        
        # create tasks
        self.test_task1 = Task(
            name='Task1',
            project=self.test_proj1,
            resources=[self.test_user1, self.test_user2],
            effort=50,
            status_list=self.test_task_status_list
        )
        DBSession.add(self.test_task1)
        DBSession.commit()
    
    def test_tjp_file_is_created(self):
        """testing if the tjp file is correctly created
        """
        # create the scheduler
        tjp_sched = TaskJugglerScheduler()
        tjp_sched.projects = [self.test_proj1]
        
        tjp_sched._create_tjp_file()
        
        # check
        self.assertTrue(os.path.exists(tjp_sched.tjp_file_full_path))
        
        # clean up the test
        tjp_sched._clean_up()
    
    def test_tjp_file_content_is_correct(self):
        """testing if the tjp file content is correct
        """
        tjp_sched = TaskJugglerScheduler()
        tjp_sched.projects = [self.test_proj1]
        
        tjp_sched._create_tjp_file()
        tjp_sched._create_tjp_file_content()
        
        import jinja2
        expected_tjp_template = jinja2.Template(
        """# Generated By Stalker v{{stalker.__version__}}
project Project_30 "Test Project 1" 2013-04-04 - 2013-05-04 {
    timingresolution 60min
    now {{now}}
    dailyworkinghours 8
    weekstartsmonday
    workinghours mon 09:30 - 18:30
    workinghours tue 09:30 - 18:30
    workinghours wed 09:30 - 18:30
    workinghours thu 09:30 - 18:30
    workinghours fri 09:30 - 18:30
    workinghours sat off
    workinghours sun off
    timeformat "%Y-%m-%d"
    scenario plan "Plan"
    trackingscenario plan
}

# resources
resource resources "Resources" {
    resource User_3 "Admin"
    resource User_14 "User1"
    resource User_16 "User2"
    resource User_17 "User3"
    resource User_19 "User4"
    resource User_20 "User5"
    resource User_21 "User6"
}

# tasks
task Project_30 "Test Project 1"{
    
    task Task_31 "Task1" {
    effort 50h
    allocate User_14, User_16
}
    
}

# bookings

# reports
taskreport breakdown "{{csv_path}}"{
    formats csv
    timeformat "%Y-%m-%d-%H:%M"
    columns id, start, end
}""")
        expected_tjp_content = expected_tjp_template.render(
            {
                'stalker': stalker,
                'now': self.test_proj1.round_time(self.test_proj1.now)
                            .strftime('%Y-%m-%d-%H:%M'),
                'csv_path': tjp_sched.temp_file_full_path
            }
        )
        
        self.maxDiff = None
        tjp_sched._clean_up()
        self.assertEqual(tjp_sched.tjp_content, expected_tjp_content)
    
    def test_tasks_are_correctly_scheduled(self):
        """testing if the tasks are correctly scheduled
        """
        tjp_sched = TaskJugglerScheduler()
        tjp_sched.projects = [self.test_proj1]
        tjp_sched.schedule()
        
        # check the task and project timings are all adjusted
        self.assertEqual(
            self.test_proj1.computed_start,
            datetime.datetime(2013, 4, 4, 10, 0)
        )
        
        self.assertEqual(
            self.test_proj1.computed_end,
            datetime.datetime(2013, 4, 8, 17, 0)
        )
        
        self.assertEqual(
            self.test_task1.computed_start,
            datetime.datetime(2013, 4, 4, 10, 0)
        )
        self.assertEqual(
            self.test_task1.computed_end,
            datetime.datetime(2013, 4, 8, 17, 0)
        )
        
    
        

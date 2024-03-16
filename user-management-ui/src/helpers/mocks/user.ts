// Copyright (C) 2024 Univention GmbH
//
// SPDX-License-Identifier: AGPL-3.0-only

import {type UsersResponse, type UserResponseData} from '@/helpers/models/user';

const exampleFirstNames = [
  'Alex',
  'Ariel',
  'Bola',
  'Charlie',
  'Cruz',
  'Dana',
  'Ira',
  'Kim',
  'Lee',
  'Lucian',
  'Quinn',
  'Rosario',
  'Sasha',
  'Taylor',
  'Tristan',
  'Yuri',
];

const exampleLastNames = [
  'Acevedo',
  'Anderson',
  'Austin',
  'Barton',
  'Blaese',
  'Brewer',
  'Burgess',
  'Campbell',
  'Carroll',
  'Carter',
  'Cartwright',
  'Chang',
  'Clarke',
  'Cortes',
  'Cunningham',
  "D'Angelo",
  'Darcy',
  'Dawson',
  'Dior',
  'Donnelly',
  'Doyle',
  'Givenchy',
  'Gonzales',
  'Graves',
  'Griffin',
  'Hampton',
  'Harding',
  'Hardy',
  'Hernandez',
  'Hicks',
  'Holmes',
  'Ibarra',
  'Indigo',
  'Jacobs',
  'Kim',
  'Knowles',
  'Larson',
  'Lee',
  'Leigh',
  'Marsh',
  'Mccarthy',
  "O'Connor",
  'Palmer',
  'Paul',
  'Perkins',
  'Pugh',
  'Rice',
  'Rico',
  'Rocha',
  'Rossi',
  'Sandoval',
  'Sainte',
  'Schofield',
  'Simmons',
  'Stafford',
  'Swanson',
  'Tate',
  'Taylor',
  'Teague',
  'Tolliver',
  'Townsend',
  'Valdez',
  'Vaughn',
  'Waller',
  'Woodward',
];

const schools = ['school-1', 'school-2', 'school-3', 'school-4', 'school-5'];

const roles = [
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'student',
  'teacher',
  'teacher',
  'staff',
  'administrator',
];

const classes = ['1a', '1b', '2a', '2b', '3a', '3b', '4a', '4b'];

const choose = (items: string[]): string => {
  return items[Math.floor(Math.random() * items.length)];
};

const usernameCounter: Record<string, number> = {};

const getUsername = (firstname: string, lastname: string): string => {
  const base = `${firstname}.${lastname}`;
  let counter = usernameCounter[base];
  if (counter === undefined) {
    usernameCounter[base] = 2;
    counter = 1;
  } else {
    usernameCounter[base] = counter + 1;
  }
  return `${base}${counter}`;
};

const isActive = (): boolean => {
  return Math.floor(Math.random() * 12) > 0;
};

const isVisible = (): boolean => {
  return Math.floor(Math.random() * 5) > 0;
};

const hasExtraSchool = (): boolean => {
  return Math.floor(Math.random() * 10) < 1;
};

const getExtraSchool = (school: string): string => {
  let newSchool = '';
  while (newSchool === '') {
    const tmpSchool = choose(schools);
    if (tmpSchool !== school) {
      newSchool = tmpSchool;
    }
  }
  return newSchool;
};

const makeRole = (roleName: string, school: string): string => {
  return `${roleName}:school:${school}`;
};

const makeClass = (className: string, school: string): string => {
  return `${className}:${school}`;
};

export const makeMockUsers = (): UserResponseData[] => {
  const numUsers = 30;
  const users: UserResponseData[] = [];

  for (let x = 1; x <= schools.length; x++) {
    for (let y = 0; y < numUsers; y++) {
      const firstname = choose(exampleFirstNames);
      const lastname = choose(exampleLastNames);
      const username = getUsername(firstname, lastname);
      const usernameIsVisible = isVisible();
      const school = schools[x - 1];
      const userSchools = [school];
      if (hasExtraSchool()) {
        userSchools.push(getExtraSchool(school));
      }
      userSchools.sort();
      const userRoles: string[] = [];
      userSchools.forEach(school => {
        const role = makeRole(choose(roles), school);
        userRoles.push(role);
      });
      const userClasses: string[] = [];
      userSchools.forEach(school => {
        const klass = makeClass(choose(classes), school);
        userClasses.push(klass);
      });
      const rolesIsVisible = isVisible();
      const active = isActive();

      users.push({
        id: username,
        attributes: {
          username: {
            access: usernameIsVisible ? 'read' : 'none',
            value: usernameIsVisible ? username : null,
          },
          firstname: {
            access: 'read',
            value: firstname,
          },
          lastname: {
            access: 'read',
            value: lastname,
          },
          roles: {
            access: rolesIsVisible ? 'read' : 'none',
            value: rolesIsVisible ? userRoles : null,
          },
          classes: {
            access: 'read',
            value: userClasses,
          },
          schools: {
            access: 'read',
            value: userSchools,
          },
          active: {
            access: 'read',
            value: active,
          },
        },
        allowedActions: ['delete'],
      });
    }
  }
  return users;
};

export const makeMockUsersResponse = (users: UserResponseData[]): UsersResponse => {
  return {
    users: users,
  };
};

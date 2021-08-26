-- What requirements can a course satisfy?
drop table if exists program_requirements cascade;
drop table if exists course_requirement_mappings;

-- Program requirements
--  name:                   the Scribe label that identifies the requirement
--  XXX_required:           how many classes/credits are required
--  conjunction:            classes AND credits versus classes OR credits
--  XXX_alternatives:       total credits/courses for all courses that can satisfy this requirement
--  context:                when requirements are nested, this is a list of enclosing context labels
--  program_qualifiers:     a list of qualifiers that apply to the entire Scribe block.
--  requirement_qualifiers: a list of qualifiers that apply to all courses specified for that
--                          requirement.
create table program_requirements (
id serial primary key,
institution text not null,
requirement_id text not null,
requirement_name text not null,
num_courses_required text not null,
course_alternatives text not null,
conjunction text,
num_credits_required text not null,
credit_alternatives text not null,
program_qualifiers jsonb not null,
requirement_qualifiers jsonb not null,
context jsonb not null,
foreign key (institution, requirement_id) references requirement_blocks,
unique (institution, requirement_id, requirement_name)
);

-- Map courses to program requirements.
-- The course_qualifiers list is for ”with” clauses within a course list.
create table course_requirement_mappings (
course_id integer,
offer_nbr integer,
program_requirement_id integer references program_requirements(id) on delete cascade,
course_qualifiers jsonb not null,
foreign key (course_id, offer_nbr) references cuny_courses,
primary key (course_id, offer_nbr, program_requirement_id)
);

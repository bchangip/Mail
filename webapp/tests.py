from django.test import TestCase
from .models import Student, StudentForm, Review, ReviewForm, Course, CourseForm, Professor, ProfessorForm, ReviewLike

# Create your tests here.

ITERATIONS = 20

class StudentTestCase(TestCase):
	def setUp(self):
		for i in range(ITERATIONS):
			Student.objects.create(
				username="test"+str(i),
				firstname="test"+str(i),
				lastname="test"+str(i),
				email="test"+str(i),
				career="test"+str(i),
				interest1="test"+str(i),
				interest2="test"+str(i),
				interest3="test"+str(i),
				highschool="test"+str(i)
			)

			Course.objects.create(
				name="test"+str(i)
			)

			Professor.objects.create(
				firstname="test"+str(i),
				lastname="test"+str(i)
			)

	def testStudents(self):
		for i in range(ITERATIONS):
			test = Student.objects.get(username="test"+str(i))
			self.assertEqual(test.username, "test"+str(i))

	def testCourse(self):
		for i in range(ITERATIONS):
			test = Course.objects.get(name="test"+str(i))
			self.assertEqual(test.name, "test"+str(i))

	def testProfessor(self):
		for i in range(ITERATIONS):
			test = Professor.objects.get(firstname="test"+str(i))
			self.assertEqual(test.lastname, "test"+str(i))


#!/usr/bin/python

import sys
import pickle
sys.path.append("../tools/")
from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data
from collections import defaultdict
from sklearn.feature_selection import SelectKBest
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.cross_validation import train_test_split, StratifiedShuffleSplit
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import classification_report
import numpy as np

### Task 1: Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = [
                 'poi','salary','bonus','ratio_of_bonus_salary','total_stock_value',
                 'exercised_stock_options','percentage_from_this_person_to_poi',
                 'shared_receipt_with_poi'
                 ] # You will need to use more features
                                  
### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)

### Task 2: Remove outliers
data_dict.pop("TOTAL")
data_dict.pop("THE TRAVEL AGENCY IN THE PARK")

### Task 3: Create new feature(s)
# Ratio of Bonus, Salary
for person, features in data_dict.iteritems():
	if features['bonus'] == "NaN" or features['salary'] == "NaN":
		features['ratio_of_bonus_salary'] = "NaN"
	else:
		features['ratio_of_bonus_salary'] = float(features['bonus']) / float(features['salary'])

# % of emails sent by the person to a POI
for person, features in data_dict.iteritems():
	if features['from_this_person_to_poi'] == "NaN" or features['from_messages'] == "NaN":
		features['percentage_from_this_person_to_poi'] = "NaN"
	else:
		features['percentage_from_this_person_to_poi'] = float(features['from_this_person_to_poi']) / float(features['from_messages'])

# % of emails sent by the POIs to the person.
for person, features in data_dict.iteritems():
	if features['from_poi_to_this_person'] == "NaN" or features['to_messages'] == "NaN":
		features['percentage_from_poi_to_this_person'] = "NaN"
	else:
		features['percentage_from_poi_to_this_person'] = float(features['from_poi_to_this_person']) / float(features['to_messages'])

### Missing Values - Imputing missing email features' values to mean
email_features_list = [
                  'to_messages', 'from_poi_to_this_person', 'from_messages',
	              'percentage_from_poi_to_this_person', 'from_this_person_to_poi',
	              'percentage_from_this_person_to_poi', 'shared_receipt_with_poi'
	             ]

email_sums = defaultdict(lambda:0)
email_counts = defaultdict(lambda:0)

for person, features in data_dict.iteritems():
	for ef in email_features_list:
		if features[ef] != "NaN":
			email_sums[ef] += features[ef]
			email_counts[ef] += 1

email_means = {}
for ef in email_features_list:
	email_means[ef] = float(email_sums[ef]) / float(email_counts[ef])

for person, features in data_dict.iteritems():
	for ef in email_features_list:
		if features[ef] == "NaN":
			features[ef] = email_means[ef]

### Store to my_dataset for easy export below.
my_dataset = data_dict

### Extract features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)

### Task 4: Try a varity of classifiers
### Please name your classifier clf for easy export below.
### Note that if you want to do PCA or other multi-stage operations,
### you'll need to use Pipelines. For more info:
### http://scikit-learn.org/stable/modules/pipeline.html

# Provided to give you a starting point. Try a variety of classifiers.
#from sklearn.naive_bayes import GaussianNB
#clf = GaussianNB()

# Algorithm pipeline
selectkbest = SelectKBest()
dtc = DecisionTreeClassifier()
svc = SVC()

steps = [('feature_selection', selectkbest), ('dtc', dtc)]

pipeline = Pipeline(steps)

parameters = dict(
                  feature_selection__k=[2, 3, 5, 6], 
                  dtc__criterion=['gini', 'entropy'],
                  dtc__max_depth=[None, 1, 2, 3, 4],
                  dtc__min_samples_split=[1, 2, 3, 4, 25],
                  dtc__class_weight=[None, 'balanced'],
                  dtc__random_state=[42]
                  )

### Task 5: Tune your classifier to achieve better than .3 precision and recall 
### using our testing script. Check the tester.py script in the final project
### folder for details on the evaluation method, especially the test_classifier
### function. Because of the small size of the dataset, the script uses
### stratified shuffle split cross validation. For more info: 
### http://scikit-learn.org/stable/modules/generated/sklearn.cross_validation.StratifiedShuffleSplit.html

# Example starting point. Try investigating other evaluation techniques!
#from sklearn.cross_validation import train_test_split
#features_train, features_test, labels_train, labels_test = \
#    train_test_split(features, labels, test_size=0.3, random_state=42)


# Create training sets and test sets
features_train, features_test, labels_train, labels_test = \
    train_test_split(features, labels, test_size=0.3, random_state=42)

# Cross-validation for parameter tuning in grid search 
s3 = StratifiedShuffleSplit(
    labels_train,
    n_iter = 20,
    test_size = 0.5,
    random_state = 0
    )

# Create, fit, and make predictions with grid search
gscv = GridSearchCV(pipeline,
	              param_grid=parameters,
	              scoring="f1",
	              cv=s3,
	              error_score=0)
gscv.fit(features_train, labels_train)
labels_predictions = gscv.predict(features_test)

# Pick the classifier with the best tuned parameters
clf = gscv.best_estimator_
print "\n", "Best parameters are: ", gscv.best_params_, "\n"

# Print features selected and their importances
features_selected=[features_list[i+1] for i in clf.named_steps['feature_selection'].get_support(indices=True)]
scores = clf.named_steps['feature_selection'].scores_
importances = clf.named_steps['dtc'].feature_importances_

indices = np.argsort(importances)[::-1]
print len(features_selected), " features:"
for i in range(len(features_selected)):
    print "{}: {} ({}) ({})".format(i+1,features_selected[indices[i]],importances[indices[i]], scores[indices[i]])

print(classification_report( labels_test, labels_predictions ))

### Task 6: Dump your classifier, dataset, and features_list so anyone can
### check your results. You do not need to change anything below, but make sure
### that the version of poi_id.py that you submit can be run on its own and
### generates the necessary .pkl files for validating your results.

dump_classifier_and_data(clf, my_dataset, features_list)

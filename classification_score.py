import pandas as pd
import os
from numpy import sum as np_sum


def total_accuracy(cm: pd.DataFrame):
    tot_labels = 0
    correct_labels = 0
    for i in range(cm.shape[0]):
        tot_labels += sum(cm.values[i, :])
        correct_labels += cm.values[i, i]

    return correct_labels / tot_labels


def producer_accuracies(cm):
    class_producer_accuracies = []
    for i in range(cm.shape[0]):
        correct_labels = cm.values[i, i]
        all_produced_labels = sum(cm.values[:, i])
        class_producer_accuracies.append(correct_labels/all_produced_labels)

    mixed_producer_accuracies = []
    if cm.shape[0] % 2 != 0:
        return class_producer_accuracies, None

    for i in range(int(cm.shape[0]/2)):
        correct_labels = np_sum(cm.values[i * 2:i*2+2, i * 2:i*2+2])
        all_produced_labels = np_sum(cm.values[:, i*2:i*2+2])
        mixed_producer_accuracies.append(correct_labels/all_produced_labels)
    return class_producer_accuracies, mixed_producer_accuracies


def user_accuracies(cm):
    class_user_accuracies = []
    for i in range(cm.shape[0]):
        correct_labels = cm.values[i, i]
        all_used_labels = sum(cm.values[i, :])
        class_user_accuracies.append(correct_labels / all_used_labels)

    if cm.shape[0] % 2 != 0:
        # print("The mixed Producer Accuracies have not been computed.")
        return class_user_accuracies, None

    mixed_user_accuracies = []
    for i in range(int(cm.shape[0] / 2)):
        correct_labels = np_sum(cm.values[i * 2:i*2+2, i * 2:i*2+2])
        all_used_labels = np_sum(cm.values[i*2: i*2+2, :])
        mixed_user_accuracies.append(correct_labels / all_used_labels)

    return class_user_accuracies, mixed_user_accuracies


def compare_confusion_matrices(directory, file_suffix='confusion.csv'):
    csv_file_list = list()
    for f in os.listdir(directory):
        if f.endswith(file_suffix):
            csv_file_list.append(f)
    print(f"{len(csv_file_list)} csv-files found.\n")

    max_score = 0
    for csv_file in csv_file_list:
        cm = pd.read_csv(os.path.join(directory, csv_file), comment='#',  header=None)
        if not cm.shape[0] == cm.shape[1]:
            raise ValueError(f"Confusion Matrix is not quadratic. I'm confused...\n{csv_file}")

        tot_acc = total_accuracy(cm)
        print(f"{csv_file}:\tTotal_Accuarcy:{tot_acc}")

        if tot_acc > max_score:
            best_classifier = csv_file
            max_score = tot_acc
            max_user_acc, max_mixed_user_acc = user_accuracies(cm)
            max_prod_acc, max_mixed_prod_acc = producer_accuracies(cm)

    print(f"\nBest classifier: {best_classifier}\nTotal Score:\t{max_score}")

    print(f"User Accuracies: {max_user_acc}")
    if max_mixed_user_acc:
        print(f"Mixed User Accuracies: {max_mixed_user_acc}")
    print(f"Producer Accuracies: {max_prod_acc}")
    if max_mixed_prod_acc:
        print(f"Mixed Producer Accuracies: {max_mixed_prod_acc}")

# # # # # # # # # # ## # # # # ## # # # # # # # # # # # # # ##  ## # # # # # # # # # # # # # # ## # # # # #
# # # # # # # # # # ##  Print Results:
# # # # # # # # # # ## # # # # ## # # # # # # # # # # # # # ##  ## # # # # # # # # # # # # # # ## # # # # #
classifier_dir = r"C:\Users\gian_\Desktop\Vegetationsklassifikation_Wieblingen\Classifier_fusion"
# classifier_dir = r"C:\Users\gian_\Desktop\Vegetationsklassifikation_Wieblingen\Classifier_optical_Kopie"
# classifier_dir = r"C:\Users\gian_\Desktop\Vegetationsklassifikation_Wieblingen\Classifier_fusion_3class"
# classifier_dir = r"C:\Users\gian_\Desktop\Vegetationsklassifikation_Wieblingen\Classifier_radar"

print(f"Directory: {classifier_dir}")
compare_confusion_matrices(classifier_dir)

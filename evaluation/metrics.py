from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


def compute_metrics(true_labels: list, predicted_labels: list) -> dict:
    """
    Compute standard classification metrics for model evaluation.

    All aggregate metrics use weighted averaging to account for class imbalance.
    zero_division=0 prevents warnings when a class has no predicted samples.
    These settings must remain fixed across runs for baseline comparability.

    Args:
        true_labels      : Ground-truth labels from the dataset.
        predicted_labels : Labels predicted by the council or a baseline.

    Returns:
        dict with accuracy, precision, recall, f1_score, and full report string.
    """
    return {
        "accuracy":  accuracy_score(true_labels, predicted_labels),
        "precision": precision_score(
            true_labels, predicted_labels,
            average="weighted", zero_division=0
        ),
        "recall":    recall_score(
            true_labels, predicted_labels,
            average="weighted", zero_division=0
        ),
        "f1_score":  f1_score(
            true_labels, predicted_labels,
            average="weighted", zero_division=0
        ),
        "report":    classification_report(
            true_labels, predicted_labels,
            zero_division=0
        )
    }

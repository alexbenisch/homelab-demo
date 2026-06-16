/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"fmt"

	appsv1k8s "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	appsv1 "github.com/alexbenisch/homelab-demo/operators/webapp-operator/api/v1"
)

// WebAppReconciler reconciles a WebApp object
type WebAppReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=apps.kubetest.uk,resources=webapps,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.kubetest.uk,resources=webapps/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.kubetest.uk,resources=webapps/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete

// Reconcile moves the current state of the cluster closer to the desired
// state described by a WebApp: it owns exactly one child Deployment and
// keeps it in sync with spec.image/replicas/port, then mirrors the
// Deployment's readiness back onto WebApp.status.
func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	webapp := &appsv1.WebApp{}
	if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	deployment := &appsv1k8s.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      webapp.Name,
			Namespace: webapp.Namespace,
		},
	}

	op, err := controllerutil.CreateOrUpdate(ctx, r.Client, deployment, func() error {
		r.applyDeploymentSpec(webapp, deployment)
		return controllerutil.SetControllerReference(webapp, deployment, r.Scheme)
	})
	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconciling deployment: %w", err)
	}
	if op != controllerutil.OperationResultNone {
		log.Info("reconciled deployment", "operation", op, "deployment", deployment.Name)
	}

	actual := &appsv1k8s.Deployment{}
	if err := r.Get(ctx, types.NamespacedName{Name: deployment.Name, Namespace: deployment.Namespace}, actual); err != nil {
		return ctrl.Result{}, fmt.Errorf("fetching deployment status: %w", err)
	}

	webapp.Status.ReadyReplicas = actual.Status.ReadyReplicas
	if err := r.Status().Update(ctx, webapp); err != nil {
		return ctrl.Result{}, fmt.Errorf("updating webapp status: %w", err)
	}

	return ctrl.Result{}, nil
}

// applyDeploymentSpec writes the desired Deployment spec for webapp onto deployment.
// It only mutates fields the operator owns, so unrelated fields set by other
// actors (e.g. autoscalers) are left untouched.
func (r *WebAppReconciler) applyDeploymentSpec(webapp *appsv1.WebApp, deployment *appsv1k8s.Deployment) {
	replicas := webapp.Spec.Replicas
	if replicas == 0 {
		replicas = 1
	}
	port := webapp.Spec.Port
	if port == 0 {
		port = 8080
	}

	labels := map[string]string{"app.kubernetes.io/name": webapp.Name}

	deployment.Spec = appsv1k8s.DeploymentSpec{
		Replicas: &replicas,
		Selector: &metav1.LabelSelector{MatchLabels: labels},
		Template: corev1.PodTemplateSpec{
			ObjectMeta: metav1.ObjectMeta{Labels: labels},
			Spec: corev1.PodSpec{
				Containers: []corev1.Container{
					{
						Name:  webapp.Name,
						Image: webapp.Spec.Image,
						Ports: []corev1.ContainerPort{
							{ContainerPort: port},
						},
					},
				},
			},
		},
	}
}

// SetupWithManager sets up the controller with the Manager.
func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1.WebApp{}).
		Owns(&appsv1k8s.Deployment{}).
		Named("webapp").
		Complete(r)
}

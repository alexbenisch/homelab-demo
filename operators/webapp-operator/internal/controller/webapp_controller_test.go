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

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	appsv1k8s "k8s.io/api/apps/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	appsv1 "github.com/alexbenisch/homelab-demo/operators/webapp-operator/api/v1"
)

var _ = Describe("WebApp Controller", func() {
	Context("When reconciling a resource", func() {
		const (
			resourceName      = "test-resource"
			resourceNamespace = "default"
		)

		ctx := context.Background()

		typeNamespacedName := types.NamespacedName{
			Name:      resourceName,
			Namespace: resourceNamespace,
		}
		webapp := &appsv1.WebApp{}

		BeforeEach(func() {
			By("creating the custom resource for the Kind WebApp")
			err := k8sClient.Get(ctx, typeNamespacedName, webapp)
			if err != nil && errors.IsNotFound(err) {
				resource := &appsv1.WebApp{
					ObjectMeta: metav1.ObjectMeta{
						Name:      resourceName,
						Namespace: resourceNamespace,
					},
					Spec: appsv1.WebAppSpec{
						Image:    "nginx:1.25",
						Replicas: 2,
						Port:     80,
					},
				}
				Expect(k8sClient.Create(ctx, resource)).To(Succeed())
			}
		})

		AfterEach(func() {
			// TODO(user): Cleanup logic after each test, like removing the resource instance.
			resource := &appsv1.WebApp{}
			err := k8sClient.Get(ctx, typeNamespacedName, resource)
			Expect(err).NotTo(HaveOccurred())

			By("Cleanup the specific resource instance WebApp")
			Expect(k8sClient.Delete(ctx, resource)).To(Succeed())
		})
		It("should successfully reconcile the resource", func() {
			By("Reconciling the created resource")
			controllerReconciler := &WebAppReconciler{
				Client: k8sClient,
				Scheme: k8sClient.Scheme(),
			}

			_, err := controllerReconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: typeNamespacedName,
			})
			Expect(err).NotTo(HaveOccurred())

			By("checking that a child Deployment was created")
			deployment := &appsv1k8s.Deployment{}
			Expect(k8sClient.Get(ctx, typeNamespacedName, deployment)).To(Succeed())
			Expect(deployment.Spec.Template.Spec.Containers[0].Image).To(Equal("nginx:1.25"))
			Expect(*deployment.Spec.Replicas).To(Equal(int32(2)))
		})
	})
})

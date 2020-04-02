#!/usr/bin/env groovy
/*
 * Jenkins Pipeline for DRAGONS
 *
 * by Bruno C. Quint
 *
 * Required Plug-ins:
 * - CloudBees File Leak Detector
 * - Cobertura Plug-in
 * - Warnings NG
 */

@Library('dragons_ci@master') _

pipeline {

    agent any

    triggers {
        pollSCM('H/6 * * * *')  // Polls Source Code Manager every six hours
    }

    options {
        skipDefaultCheckout(true)
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    environment {
        PATH = "$JENKINS_HOME/anaconda3/bin:$PATH"
        MPLBACKEND = "agg"
        // CONDA_ENV_FILE = ".jenkins/conda_py3env_stable.yml"
        // CONDA_ENV_NAME = "py3_stable"
        // PYTEST_ARGS = "--remote-data=any --basetemp=/data/jenkins/dragons/outputs"
    }

    stages {
        stage ("Prepare"){
            steps{
                sendNotifications 'STARTED'
            }
        }

        stage('Code Metrics') {
            when {
                branch 'master'
            }
            steps {
                echo "Running ${env.BUILD_ID} on ${env.JENKINS_URL}"
                checkout scm
                sh '.jenkins/scripts/setup_agent.sh'
                sh 'tox -e check'
            }
            post {
                success {
                    recordIssues(
                        enabledForFailure: true,
                        tools: [
                            pyLint(pattern: '**/reports/pylint.log'),
                            pyDocStyle(pattern: '**/reports/pydocstyle.log')
                        ]
                    )
                }
            }
        }

        parallel {
            stage('Unit tests - MacOS/Python 3.6') {
                agent{
                    label "macos"
                }
                steps {
                    echo "Running ${env.BUILD_ID} on ${env.JENKINS_URL}"
                    checkout scm
                    sh '.jenkins/scripts/setup_agent.sh'
                    echo "Running tests with Python 3.6 and older dependencies"
                    sh 'tox -e py36-unit-olddeps -v -- --junit-xml reports/unittests_results.xml'
                    echo "Reportint coverage to CodeCov"
                    sh 'tox -e codecov -- -F unit'
                }
            }

            stage('Unit tests - Linux/Python 3.7') {
                agent{
                    label "centos7"
                }
                steps {
                    echo "Running ${env.BUILD_ID} on ${env.JENKINS_URL}"
                    checkout scm
                    sh '.jenkins/scripts/setup_agent.sh'
                    echo "Running tests with Python 3.7"
                    sh 'tox -e py37-unit -v -- --junit-xml reports/unittests_results.xml'
                    echo "Reportint coverage to CodeCov"
                    sh 'tox -e codecov -- -F unit'
                }
            }
        }

        stage('Integration tests') {
            // when {
            //     branch 'master'
            // }
            agent {
                label "centos7"
            }
            steps {
                echo "Running ${env.BUILD_ID} on ${env.JENKINS_URL}"
                checkout scm
                sh '.jenkins/scripts/setup_agent.sh'
                echo "Integration tests"
                sh 'tox -e py36-integ -v -- --junit-xml reports/integration_results.xml'
                echo "Reporting coverage"
                sh 'tox -e codecov -- -F integration'
            }
        }

        stage('GMOS LS Tests') {
            agent {
                label "centos7"
            }
            steps {
                echo "Running ${env.BUILD_ID} on ${env.JENKINS_URL}"
                checkout scm
                sh '.jenkins/scripts/setup_agent.sh'
                echo "Running tests"
                sh 'tox -e py36-gmosls -v -- --junit-xml reports/unittests_results.xml'
                echo "Reporting coverage"
                sh 'tox -e codecov -- -F gmosls'
            }  // end steps
            post {
                always {
                    echo "Running 'archivePlots' from inside GmosArcTests"
                    archiveArtifacts artifacts: "plots/*", allowEmptyArchive: true
                }  // end always
            }  // end post
        }  // end stage

    }
    post {
        always {
          junit (
            allowEmptyResults: true,
            testResults: 'reports/*_results.xml'
            )
        }
        success {
//             sh  '.jenkins/scripts/build_sdist_file.sh'
//             sh  'pwd'
//             echo 'Make tarball available'
            sendNotifications 'SUCCESSFUL'
        }
        failure {
            sendNotifications 'FAILED'
        }
    }
}

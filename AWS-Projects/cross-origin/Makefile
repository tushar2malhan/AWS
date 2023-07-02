
.PHONY: help lint lint-fix image push run deploy clean
.DEFAULT_GOAL := help
python_error_file = code_errors.txt

test: ## 🧪  Run tests
    
	flake8 --version
	flake8 . --exit-zero 
	flake8 . --exit-zero > $(python_error_file)

plan: ## 📝  Plan terraform
	
	echo "Printing all files in the prep blue directory"
	cd automation/ca-central-1/mon-prep-blue/lambda && \
	ls -la && \
	terraform init -input=false --upgrade  && \
	terraform validate && \
	terraform fmt && \
	touch mon-prep-blue-tfplan && \
	terraform plan -out mon-prep-blue-tfplan -input=false 


# ========================= PREP ACCOUNTS ===========================================

prep-blue/deploy: ## 🚀  Apply terraform in Prep
	
	echo "Deployment in Prep account"
	cd automation/ca-central-1/mon-prep-blue/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prep-blue-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prep-blue-tfplan

prep-grey/deploy: ## 🚀  Apply terraform in Prep
	
	echo "Deployment in Prep account"
	cd automation/ca-central-1/mon-prep-grey/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prep-grey-tfplan -input=false && \
	terraform apply -input=false -auto-approve mon-prep-grey-tfplan


prep-yellow/deploy: ## 🚀  Apply terraform in Prep
	
	echo "Deployment in Prep account"
	cd automation/ca-central-1/mon-prep-yellow/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prep-yellow-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prep-yellow-tfplan

# ========================= PROD ACCOUNTS ===========================================

prod-blue/deploy: ## 🚀  Apply terraform in Prod
	
	echo "Deployment in Prod account"
	cd automation/ca-central-1/mon-prod-blue/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prod-blue-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prod-blue-tfplan

prod-grey/deploy: ## 🚀  Apply terraform in Prod
	
	echo "Deployment in Prod account"
	cd automation/ca-central-1/mon-prod-grey/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prod-grey-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prod-grey-tfplan

prod-yellow/deploy: ## 🚀  Apply terraform in Prod
	
	echo "Deployment in Prod account"
	cd automation/ca-central-1/mon-prod-yellow/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prod-yellow-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prod-yellow-tfplan

	
clean:  ## 🧹 Clean up project

	rm -fr .terraform
	rm -rf .venv
	rm -rf .pytest_cache


# ============================================================================

''' a comprehensive Python program for AI applications in Sales that covers lead scoring, sales forecasting, pricing optimization, and customer relationship management.'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.cluster import KMeans
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class AISalesAssistant:
    def __init__(self):
        self.lead_data = None
        self.sales_data = None
        self.customer_data = None
        self.product_data = None
        self.models = {}
       
    def generate_synthetic_data(self):
        """Generate synthetic data for demonstration purposes"""
        np.random.seed(42)
       
        # Generate lead data
        n_leads = 1000
        self.lead_data = pd.DataFrame({
            'lead_id': range(1, n_leads + 1),
            'industry': np.random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'], n_leads),
            'company_size': np.random.choice(['Small', 'Medium', 'Large', 'Enterprise'], n_leads, p=[0.4, 0.3, 0.2, 0.1]),
            'annual_revenue': np.random.lognormal(15, 1, n_leads),
            'website_visits': np.random.poisson(10, n_leads),
            'email_opens': np.random.poisson(5, n_leads),
            'meetings_attended': np.random.poisson(1, n_leads),
            'days_since_first_contact': np.random.randint(1, 365, n_leads),
            'number_of_contacts': np.random.poisson(3, n_leads),
            'source': np.random.choice(['Web', 'Referral', 'Event', 'Cold Call', 'Advertisement'], n_leads),
            'decision_maker_level': np.random.choice(['C-Level', 'VP', 'Director', 'Manager', 'Other'], n_leads),
            'budget_confirmed': np.random.choice([0, 1], n_leads, p=[0.6, 0.4]),
            'competitor_analysis': np.random.choice([0, 1], n_leads, p=[0.5, 0.5]),
            'converted': np.random.choice([0, 1], n_leads, p=[0.7, 0.3])
        })
       
        # Generate historical sales data (time series)
        n_months = 36
        dates = pd.date_range(start='2021-01-01', periods=n_months, freq='ME')
       
        # Create sales trends with seasonality
        trend = np.linspace(100000, 200000, n_months)
        seasonality = 50000 * np.sin(np.linspace(0, 6*np.pi, n_months))
        noise = np.random.normal(0, 10000, n_months)
        sales_values = trend + seasonality + noise
       
        self.sales_data = pd.DataFrame({
            'date': dates,
            'sales': sales_values,
            'num_deals': np.random.poisson(20, n_months),
            'avg_deal_size': sales_values / np.random.poisson(20, n_months)
        })
       
        # Generate customer data
        n_customers = 500
        self.customer_data = pd.DataFrame({
            'customer_id': range(1, n_customers + 1),
            'company_name': [f'Company_{i}' for i in range(1, n_customers + 1)],
            'industry': np.random.choice(['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'], n_customers),
            'customer_since': pd.date_range(start='2019-01-01', periods=n_customers, freq='D'),
            'total_purchases': np.random.lognormal(12, 1, n_customers),
            'purchase_frequency': np.random.poisson(3, n_customers),
            'satisfaction_score': np.random.uniform(1, 10, n_customers),
            'customer_type': np.random.choice(['Premium', 'Standard', 'Basic'], n_customers, p=[0.2, 0.5, 0.3]),
            'churn_risk': np.random.uniform(0, 1, n_customers),
            'last_purchase_date': pd.date_range(end='2024-01-01', periods=n_customers, freq='D'),
            'support_tickets': np.random.poisson(2, n_customers),
            'contract_renewal_date': pd.date_range(start='2024-01-01', periods=n_customers, freq='D'),
            'lifetime_value': np.random.lognormal(13, 1, n_customers)
        })
       
        # Generate product data for pricing optimization
        n_products = 50
        self.product_data = pd.DataFrame({
            'product_id': range(1, n_products + 1),
            'product_name': [f'Product_{i}' for i in range(1, n_products + 1)],
            'category': np.random.choice(['Software', 'Hardware', 'Service', 'Subscription'], n_products),
            'current_price': np.random.uniform(100, 10000, n_products),
            'cost': np.random.uniform(50, 5000, n_products),
            'demand_elasticity': np.random.uniform(-2, -0.5, n_products),
            'competitor_price': np.random.uniform(100, 10000, n_products),
            'current_sales_volume': np.random.poisson(100, n_products),
            'inventory_level': np.random.poisson(500, n_products),
            'market_share': np.random.uniform(0.05, 0.5, n_products)
        })
       
        print("Synthetic data generated successfully!")
       
    # 1. LEAD SCORING
    def build_lead_scoring_model(self):
        """Build a lead scoring model using Random Forest"""
        print("\n----- LEAD SCORING MODEL -----")
       
        if self.lead_data is None:
            print("Generating synthetic lead data...")
            self.generate_synthetic_data()
       
        # Prepare features and target
        feature_columns = ['website_visits', 'email_opens', 'meetings_attended',
                          'days_since_first_contact', 'number_of_contacts',
                          'budget_confirmed', 'competitor_analysis']
       
        # Encode categorical variables
        encoded_data = self.lead_data.copy()
        label_encoders = {}
       
        categorical_columns = ['industry', 'company_size', 'source', 'decision_maker_level']
        for col in categorical_columns:
            le = LabelEncoder()
            encoded_data[col] = le.fit_transform(encoded_data[col])
            label_encoders[col] = le
            feature_columns.append(col)
       
        # Scale annual revenue
        encoded_data['annual_revenue_scaled'] = np.log1p(encoded_data['annual_revenue'])
        feature_columns.append('annual_revenue_scaled')
       
        # Prepare data for modeling
        X = encoded_data[feature_columns]
        y = encoded_data['converted']
       
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
       
        # Train model
        lead_scoring_model = RandomForestClassifier(n_estimators=100, random_state=42)
        lead_scoring_model.fit(X_train, y_train)
       
        # Evaluate model
        y_pred = lead_scoring_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
       
        # Calculate lead scores (probability of conversion)
        lead_scores = lead_scoring_model.predict_proba(X)[:, 1]
        self.lead_data['lead_score'] = lead_scores * 100  # Convert to 0-100 scale
       
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_columns,
            'importance': lead_scoring_model.feature_importances_
        }).sort_values('importance', ascending=False)
       
        print(f"Lead Scoring Model Accuracy: {accuracy:.2f}")
        print("\nTop 5 Features for Lead Scoring:")
        print(feature_importance.head())
       
        # Categorize leads based on scores
        self.lead_data['lead_priority'] = pd.cut(
            self.lead_data['lead_score'],
            bins=[0, 30, 60, 80, 100],
            labels=['Cold', 'Warm', 'Hot', 'Very Hot']
        )
       
        # Display lead score distribution
        plt.figure(figsize=(10, 6))
        plt.subplot(1, 2, 1)
        plt.hist(self.lead_data['lead_score'], bins=20, edgecolor='black')
        plt.xlabel('Lead Score')
        plt.ylabel('Count')
        plt.title('Lead Score Distribution')
       
        plt.subplot(1, 2, 2)
        priority_counts = self.lead_data['lead_priority'].value_counts()
        plt.bar(priority_counts.index, priority_counts.values)
        plt.xlabel('Lead Priority')
        plt.ylabel('Count')
        plt.title('Lead Priority Distribution')
        plt.tight_layout()
        plt.show()
       
        self.models['lead_scoring'] = lead_scoring_model
       
        # Return top leads
        top_leads = self.lead_data.nlargest(10, 'lead_score')[
            ['lead_id', 'industry', 'company_size', 'lead_score', 'lead_priority']
        ]
       
        print("\nTop 10 Leads:")
        print(top_leads)
       
        return lead_scoring_model, feature_importance
   
    # 2. SALES FORECASTING
    def build_sales_forecast(self, forecast_months=12):
        """Build sales forecasting models"""
        print("\n----- SALES FORECASTING -----")
       
        if self.sales_data is None:
            print("Generating synthetic sales data...")
            self.generate_synthetic_data()
       
        # Prepare features for time series forecasting
        sales_df = self.sales_data.copy()
        sales_df.set_index('date', inplace=True)
       
        # Create time-based features
        sales_df['month'] = sales_df.index.month
        sales_df['year'] = sales_df.index.year
        sales_df['quarter'] = sales_df.index.quarter
        sales_df['day_of_week'] = sales_df.index.dayofweek
        sales_df['is_month_end'] = sales_df.index.is_month_end.astype(int)
       
        # Create lag features
        for lag in [1, 3, 6, 12]:
            sales_df[f'sales_lag_{lag}'] = sales_df['sales'].shift(lag)
            sales_df[f'deals_lag_{lag}'] = sales_df['num_deals'].shift(lag)
       
        # Create rolling statistics
        for window in [3, 6, 12]:
            sales_df[f'sales_rolling_mean_{window}'] = sales_df['sales'].rolling(window=window).mean()
            sales_df[f'sales_rolling_std_{window}'] = sales_df['sales'].rolling(window=window).std()
       
        # Remove rows with NaN values
        sales_df.dropna(inplace=True)
       
        # Prepare features and target
        feature_columns = [col for col in sales_df.columns if col not in ['sales', 'num_deals', 'avg_deal_size']]
        X = sales_df[feature_columns]
        y = sales_df['sales']
       
        # Train-test split (keeping time order)
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
       
        # Train forecasting model
        forecast_model = RandomForestRegressor(n_estimators=100, random_state=42)
        forecast_model.fit(X_train, y_train)
       
        # Evaluate model
        y_pred = forecast_model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
       
        print(f"Sales Forecast Model Performance:")
        print(f"Mean Squared Error: {mse:.2f}")
        print(f"R² Score: {r2:.2f}")
       
        # Generate future forecast
        last_date = sales_df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1),
                                    periods=forecast_months, freq='ME')
       
        future_df = pd.DataFrame(index=future_dates)
        future_df['month'] = future_df.index.month
        future_df['year'] = future_df.index.year
        future_df['quarter'] = future_df.index.quarter
        future_df['day_of_week'] = future_df.index.dayofweek
        future_df['is_month_end'] = future_df.index.is_month_end.astype(int)
       
        # Forecast future sales (simplified approach)
        last_known_values = sales_df.iloc[-1]
        for i in range(len(future_df)):
            # Use last known values for lag features
            for lag in [1, 3, 6, 12]:
                if i >= lag:
                    future_df.loc[future_df.index[i], f'sales_lag_{lag}'] = future_df.loc[future_df.index[i-lag], 'forecast'] if 'forecast' in future_df.columns else last_known_values['sales']
                else:
                    future_df.loc[future_df.index[i], f'sales_lag_{lag}'] = last_known_values['sales']
                future_df.loc[future_df.index[i], f'deals_lag_{lag}'] = last_known_values['num_deals']
           
            # Use last known values for rolling statistics
            for window in [3, 6, 12]:
                future_df.loc[future_df.index[i], f'sales_rolling_mean_{window}'] = last_known_values[f'sales_rolling_mean_{window}']
                future_df.loc[future_df.index[i], f'sales_rolling_std_{window}'] = last_known_values[f'sales_rolling_std_{window}']
           
            # Make prediction
            X_future = future_df.loc[[future_df.index[i]], feature_columns]
            future_df.loc[future_df.index[i], 'forecast'] = forecast_model.predict(X_future)[0]
       
        # Plot results
        plt.figure(figsize=(12, 6))
        plt.plot(sales_df.index, sales_df['sales'], label='Historical Sales', color='blue')
        plt.plot(future_df.index, future_df['forecast'], label='Forecasted Sales',
                color='red', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('Sales')
        plt.title('Sales Forecast')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
       
        # Calculate forecast metrics
        forecast_summary = pd.DataFrame({
            'date': future_df.index,
            'forecast': future_df['forecast'],
            'month': future_df.index.strftime('%B %Y')
        })
       
        print("\nSales Forecast for Next 3 Months:")
        print(forecast_summary.head(3))
       
        self.models['sales_forecast'] = forecast_model
       
        return forecast_model, forecast_summary
   
    # 3. PRICING OPTIMIZATION
    def optimize_pricing(self):
        """Optimize product pricing to maximize profit"""
        print("\n----- PRICING OPTIMIZATION -----")
       
        if self.product_data is None:
            print("Generating synthetic product data...")
            self.generate_synthetic_data()
       
        # Dynamic pricing optimization for each product
        optimized_prices = []
       
        for _, product in self.product_data.iterrows():
            # Define profit function based on price elasticity
            def profit_function(price):
                # Calculate expected demand based on price elasticity
                price_ratio = price / product['current_price']
                demand_multiplier = price_ratio ** product['demand_elasticity']
                expected_volume = product['current_sales_volume'] * demand_multiplier
               
                # Calculate profit
                profit = (price - product['cost']) * expected_volume
               
                return -profit  # Negative because we minimize
           
            # Constraints
            def demand_constraint(price):
                # Ensure demand doesn't fall below 20% of current volume
                price_ratio = price / product['current_price']
                demand_multiplier = price_ratio ** product['demand_elasticity']
                return demand_multiplier - 0.2
           
            # Set bounds for optimization
            min_price = product['cost'] * 1.1  # At least 10% markup
            max_price = product['competitor_price'] * 1.2  # Not more than 20% above competitor
           
            # Optimize
            result = minimize(
                profit_function,
                x0=product['current_price'],
                bounds=[(min_price, max_price)],
                constraints=[{'type': 'ineq', 'fun': demand_constraint}]
            )
           
            optimized_price = result.x[0]
           
            # Calculate expected impact
            price_ratio = optimized_price / product['current_price']
            demand_multiplier = price_ratio ** product['demand_elasticity']
            expected_volume = product['current_sales_volume'] * demand_multiplier
            current_profit = (product['current_price'] - product['cost']) * product['current_sales_volume']
            optimized_profit = (optimized_price - product['cost']) * expected_volume
            profit_increase = (optimized_profit - current_profit) / current_profit * 100
           
            optimized_prices.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'current_price': product['current_price'],
                'optimized_price': optimized_price,
                'price_change_pct': (optimized_price - product['current_price']) / product['current_price'] * 100,
                'expected_volume_change_pct': (expected_volume - product['current_sales_volume']) / product['current_sales_volume'] * 100,
                'profit_increase_pct': profit_increase
            })
       
        # Convert to DataFrame
        pricing_results = pd.DataFrame(optimized_prices)
       
        # Add optimized prices to product data
        self.product_data = self.product_data.merge(
            pricing_results[['product_id', 'optimized_price', 'price_change_pct', 'profit_increase_pct']],
            on='product_id'
        )
       
        # Visualize results
        plt.figure(figsize=(14, 8))
       
        # Price change distribution
        plt.subplot(2, 2, 1)
        plt.hist(pricing_results['price_change_pct'], bins=20, edgecolor='black')
        plt.xlabel('Price Change (%)')
        plt.ylabel('Number of Products')
        plt.title('Distribution of Price Changes')
       
        # Profit increase distribution
        plt.subplot(2, 2, 2)
        plt.hist(pricing_results['profit_increase_pct'], bins=20, edgecolor='black')
        plt.xlabel('Profit Increase (%)')
        plt.ylabel('Number of Products')
        plt.title('Distribution of Profit Increases')
       
        # Top products by profit increase
        plt.subplot(2, 2, 3)
        top_10_profit = pricing_results.nlargest(10, 'profit_increase_pct')
        plt.barh(top_10_profit['product_name'], top_10_profit['profit_increase_pct'])
        plt.xlabel('Profit Increase (%)')
        plt.title('Top 10 Products by Profit Increase')
       
        # Price vs Profit Increase
        plt.subplot(2, 2, 4)
        plt.scatter(pricing_results['price_change_pct'], pricing_results['profit_increase_pct'])
        plt.xlabel('Price Change (%)')
        plt.ylabel('Profit Increase (%)')
        plt.title('Price Change vs Profit Increase')
       
        plt.tight_layout()
        plt.show()
       
        # Print summary statistics
        print(f"Average price change: {pricing_results['price_change_pct'].mean():.1f}%")
        print(f"Average profit increase: {pricing_results['profit_increase_pct'].mean():.1f}%")
        print(f"Products with price increase: {(pricing_results['price_change_pct'] > 0).sum()}")
        print(f"Products with price decrease: {(pricing_results['price_change_pct'] < 0).sum()}")
       
        # Display top opportunities
        print("\nTop 10 Pricing Opportunities (by profit increase):")
        print(top_10_profit[['product_name', 'current_price', 'optimized_price',
                            'price_change_pct', 'profit_increase_pct']])
       
        return pricing_results
   
    # 4. CUSTOMER RELATIONSHIP MANAGEMENT
    def analyze_customer_relationships(self):
        """Analyze customer relationships and identify opportunities"""
        print("\n----- CUSTOMER RELATIONSHIP MANAGEMENT -----")
       
        if self.customer_data is None:
            print("Generating synthetic customer data...")
            self.generate_synthetic_data()
       
        # 1. Customer Segmentation using RFM Analysis
        current_date = pd.Timestamp.now()
       
        # Calculate RFM metrics
        self.customer_data['recency'] = (current_date - self.customer_data['last_purchase_date']).dt.days
        self.customer_data['frequency'] = self.customer_data['purchase_frequency']
        self.customer_data['monetary'] = self.customer_data['total_purchases']
       
        # Normalize RFM values
        rfm_features = ['recency', 'frequency', 'monetary']
        scaler = StandardScaler()
        rfm_normalized = scaler.fit_transform(self.customer_data[rfm_features])
       
        # Perform customer segmentation
        kmeans = KMeans(n_clusters=4, random_state=42)
        self.customer_data['customer_segment'] = kmeans.fit_predict(rfm_normalized)
       
        # Label segments
        segment_labels = ['Champions', 'Loyal Customers', 'Potential Loyalists', 'At Risk']
        self.customer_data['segment_label'] = self.customer_data['customer_segment'].map(
            lambda x: segment_labels[x])
       
        # 2. Churn Risk Analysis
        # Build churn prediction model
        churn_features = ['purchase_frequency', 'total_purchases', 'satisfaction_score',
                         'support_tickets', 'recency']
       
        X_churn = self.customer_data[churn_features]
        y_churn = (self.customer_data['churn_risk'] > 0.7).astype(int)  # High risk threshold
       
        churn_model = LogisticRegression(random_state=42)
        churn_model.fit(X_churn, y_churn)
       
        # Predict churn probability
        self.customer_data['churn_probability'] = churn_model.predict_proba(X_churn)[:, 1]
       
        # 3. Customer Lifetime Value Prediction
        clv_features = ['total_purchases', 'purchase_frequency', 'customer_type',
                       'satisfaction_score']
       
        # Encode customer type
        le = LabelEncoder()
        clv_data = self.customer_data.copy()
        clv_data['customer_type_encoded'] = le.fit_transform(clv_data['customer_type'])
       
        X_clv = clv_data[['total_purchases', 'purchase_frequency',
                         'customer_type_encoded', 'satisfaction_score']]
        y_clv = clv_data['lifetime_value']
       
        clv_model = RandomForestRegressor(n_estimators=100, random_state=42)
        clv_model.fit(X_clv, y_clv)
       
        # Predict CLV
        self.customer_data['predicted_clv'] = clv_model.predict(X_clv)
       
        # 4. Next Best Action Recommendations
        self.customer_data['next_best_action'] = self.customer_data.apply(
            self._determine_next_best_action, axis=1)
       
        # Visualize results
        plt.figure(figsize=(16, 12))
       
        # Customer segment distribution
        plt.subplot(2, 2, 1)
        segment_counts = self.customer_data['segment_label'].value_counts()
        plt.pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%')
        plt.title('Customer Segment Distribution')
       
        # Churn risk by segment
        plt.subplot(2, 2, 2)
        sns.boxplot(data=self.customer_data, x='segment_label', y='churn_probability')
        plt.xticks(rotation=45)
        plt.title('Churn Risk by Customer Segment')
        plt.ylabel('Churn Probability')
       
        # CLV by segment
        plt.subplot(2, 2, 3)
        sns.boxplot(data=self.customer_data, x='segment_label', y='predicted_clv')
        plt.xticks(rotation=45)
        plt.title('Customer Lifetime Value by Segment')
        plt.ylabel('Predicted CLV')
       
        # RFM scatter plot
        plt.subplot(2, 2, 4)
        scatter = plt.scatter(self.customer_data['recency'],
                            self.customer_data['frequency'],
                            c=self.customer_data['customer_segment'],
                            s=self.customer_data['monetary']/1000,
                            alpha=0.6,
                            cmap='viridis')
        plt.xlabel('Recency (days)')
        plt.ylabel('Frequency')
        plt.title('RFM Analysis')
        plt.colorbar(scatter, label='Segment')
       
        plt.tight_layout()
        plt.show()
       
        # Generate actionable insights
        print("\nCustomer Relationship Insights:")
       
        # High-value customers at risk
        at_risk_valuable = self.customer_data[
            (self.customer_data['churn_probability'] > 0.6) &
            (self.customer_data['predicted_clv'] > self.customer_data['predicted_clv'].quantile(0.75))
        ]
       
        print(f"\nHigh-value customers at risk of churn: {len(at_risk_valuable)}")
        print("Top 5 at-risk valuable customers:")
        print(at_risk_valuable.nlargest(5, 'predicted_clv')[
            ['customer_id', 'company_name', 'predicted_clv', 'churn_probability', 'next_best_action']
        ])
       
        # Contract renewal opportunities
        renewal_soon = self.customer_data[
            (self.customer_data['contract_renewal_date'] - current_date).dt.days < 90
        ]
       
        print(f"\nContracts up for renewal in next 90 days: {len(renewal_soon)}")
        print("Top 5 renewal opportunities by CLV:")
        print(renewal_soon.nlargest(5, 'predicted_clv')[
            ['customer_id', 'company_name', 'contract_renewal_date', 'predicted_clv', 'next_best_action']
        ])
       
        # Segment-specific strategies
        print("\nRecommended Strategies by Segment:")
        segment_strategies = {
            'Champions': 'VIP treatment, exclusive offers, loyalty rewards',
            'Loyal Customers': 'Cross-sell opportunities, referral programs',
            'Potential Loyalists': 'Engagement campaigns, product education',
            'At Risk': 'Win-back campaigns, special retention offers'
        }
       
        for segment, strategy in segment_strategies.items():
            count = (self.customer_data['segment_label'] == segment).sum()
            print(f"{segment} ({count} customers): {strategy}")
       
        # Store models
        self.models['churn_prediction'] = churn_model
        self.models['clv_prediction'] = clv_model
        self.models['customer_segmentation'] = kmeans
       
        return {
            'customer_data': self.customer_data,
            'at_risk_valuable': at_risk_valuable,
            'renewal_opportunities': renewal_soon
        }
   
    def _determine_next_best_action(self, customer):
        """Determine the next best action for a customer"""
        if customer['churn_probability'] > 0.7:
            return 'Retention campaign - High churn risk'
        elif customer['satisfaction_score'] < 5:
            return 'Service recovery - Low satisfaction'
        elif customer['recency'] > 180:
            return 'Re-engagement campaign - Inactive customer'
        elif customer['predicted_clv'] > customer['lifetime_value'] * 1.5:
            return 'Upsell opportunity - High potential value'
        elif (customer['contract_renewal_date'] - pd.Timestamp.now()).days < 90:
            return 'Renewal preparation - Contract expiring soon'
        else:
            return 'Standard follow-up - Maintain relationship'
   
    def generate_sales_insights(self):
        """Generate comprehensive sales insights and recommendations"""
        print("\n----- SALES INSIGHTS DASHBOARD -----")
       
        if not all([self.lead_data is not None,
                   self.sales_data is not None,
                   self.customer_data is not None,
                   self.product_data is not None]):
            print("Loading all required data...")
            self.generate_synthetic_data()
            self.build_lead_scoring_model()
            self.build_sales_forecast()
            self.optimize_pricing()
            self.analyze_customer_relationships()
       
        # 1. Pipeline Health
        print("\n📊 Sales Pipeline Health:")
        pipeline_summary = self.lead_data.groupby('lead_priority').agg({
            'lead_id': 'count',
            'lead_score': 'mean',
            'annual_revenue': 'sum'
        }).rename(columns={
            'lead_id': 'count',
            'lead_score': 'avg_score',
            'annual_revenue': 'potential_revenue'
        })
       
        print(pipeline_summary)
       
        # 2. Revenue Forecast (continued)
        if 'sales_forecast' in self.models:
            print("\n📈 Revenue Forecast:")
            # Get the forecast data we created earlier
            sales_forecast = self.models.get('forecast_summary', None)
            if sales_forecast is not None:
                next_3_months = sales_forecast.head(3)
                total_forecasted = next_3_months['forecast'].sum()
                print(f"Total forecasted revenue (next 3 months): ${total_forecasted:,.2f}")
        
        # 3. Customer Health
        print("\n👥 Customer Health Overview:")
        customer_health = self.customer_data.groupby('segment_label').agg({
            'customer_id': 'count',
            'churn_probability': 'mean',
            'predicted_clv': 'mean',
            'satisfaction_score': 'mean'
        }).rename(columns={
            'customer_id': 'customer_count',
            'churn_probability': 'avg_churn_risk',
            'predicted_clv': 'avg_clv',
            'satisfaction_score': 'avg_satisfaction'
        })
        
        print(customer_health)
        
        # 4. Product Performance
        print("\n📦 Product Performance:")
        if 'optimized_price' in self.product_data.columns:
            product_performance = self.product_data.nlargest(5, 'profit_increase_pct')[
                ['product_name', 'current_price', 'optimized_price', 
                 'profit_increase_pct']
            ]
            print("Top 5 pricing optimization opportunities:")
            print(product_performance)
        
        # 5. Action Items
        print("\n🎯 Recommended Actions:")
        
        # Priority leads to contact
        hot_leads = self.lead_data[self.lead_data['lead_priority'] == 'Very Hot'].head(5)
        print(f"\n1. Priority Leads to Contact ({len(hot_leads)}):")
        for _, lead in hot_leads.iterrows():
            print(f"   - Lead {lead['lead_id']}: {lead['industry']} ({lead['lead_score']:.1f} score)")
        
        # At-risk customers
        high_risk_customers = self.customer_data[
            self.customer_data['churn_probability'] > 0.7
        ].head(5)
        print(f"\n2. High-Risk Customers to Engage ({len(high_risk_customers)}):")
        for _, customer in high_risk_customers.iterrows():
            print(f"   - {customer['company_name']}: {customer['next_best_action']}")
        
        # Renewal opportunities
        renewals = self.customer_data[
            ((self.customer_data['contract_renewal_date'] - pd.Timestamp.now()).dt.days < 90) &
            ((self.customer_data['contract_renewal_date'] - pd.Timestamp.now()).dt.days > 0)
        ].head(5)
        print(f"\n3. Upcoming Renewals ({len(renewals)}):")
        for _, customer in renewals.iterrows():
            days_until = (customer['contract_renewal_date'] - pd.Timestamp.now()).days
            print(f"   - {customer['company_name']}: {days_until} days until renewal")
        
        # Pricing adjustments
        if 'optimized_price' in self.product_data.columns:
            pricing_actions = self.product_data.nlargest(3, 'profit_increase_pct')
            print("\n4. Recommended Pricing Adjustments:")
            for _, product in pricing_actions.iterrows():
                print(f"   - {product['product_name']}: "
                      f"${product['current_price']:.2f} → ${product['optimized_price']:.2f} "
                      f"(+{product['profit_increase_pct']:.1f}% profit)")
        
        # Create a visual dashboard
        self._create_sales_dashboard()
    
    def _create_sales_dashboard(self):
        """Create a comprehensive sales dashboard"""
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Lead Funnel
        ax1 = plt.subplot(2, 3, 1)
        lead_funnel = self.lead_data['lead_priority'].value_counts().sort_index()
        colors = ['#ff9999', '#ffcc99', '#99ff99', '#66b3ff']
        bars = ax1.bar(lead_funnel.index, lead_funnel.values, color=colors)
        ax1.set_title('Lead Funnel')
        ax1.set_ylabel('Number of Leads')
        
        # Add values on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 2. Sales Forecast
        ax2 = plt.subplot(2, 3, 2)
        if hasattr(self, 'sales_data'):
            historical = self.sales_data.tail(12)
            ax2.plot(historical['date'], historical['sales'], 
                    marker='o', label='Historical', color='blue')
            
            if 'sales_forecast' in self.models:
                forecast_data = self.models.get('forecast_summary', pd.DataFrame())
                if not forecast_data.empty:
                    ax2.plot(forecast_data['date'].head(6), 
                            forecast_data['forecast'].head(6),
                            marker='o', linestyle='--', 
                            label='Forecast', color='red')
            
            ax2.set_title('Sales Trend & Forecast')
            ax2.set_ylabel('Sales ($)')
            ax2.legend()
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Customer Segments
        ax3 = plt.subplot(2, 3, 3)
        segment_sizes = self.customer_data['segment_label'].value_counts()
        wedges, texts, autotexts = ax3.pie(segment_sizes.values, 
                                          labels=segment_sizes.index,
                                          autopct='%1.1f%%',
                                          colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
        ax3.set_title('Customer Segments')
        
        # 4. Churn Risk Distribution
        ax4 = plt.subplot(2, 3, 4)
        ax4.hist(self.customer_data['churn_probability'], 
                bins=20, edgecolor='black', color='salmon')
        ax4.axvline(x=0.7, color='red', linestyle='--', label='High Risk Threshold')
        ax4.set_title('Churn Risk Distribution')
        ax4.set_xlabel('Churn Probability')
        ax4.set_ylabel('Number of Customers')
        ax4.legend()
        
        # 5. CLV by Segment
        ax5 = plt.subplot(2, 3, 5)
        segments = self.customer_data['segment_label'].unique()
        clv_by_segment = [self.customer_data[self.customer_data['segment_label'] == seg]['predicted_clv'].mean() 
                         for seg in segments]
        bars = ax5.bar(segments, clv_by_segment, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
        ax5.set_title('Average CLV by Segment')
        ax5.set_ylabel('Predicted CLV ($)')
        ax5.tick_params(axis='x', rotation=45)
        
        # Add values on bars
        for bar in bars:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'${int(height):,}', ha='center', va='bottom')
        
        # 6. Product Pricing Impact
        ax6 = plt.subplot(2, 3, 6)
        if 'profit_increase_pct' in self.product_data.columns:
            top_products = self.product_data.nlargest(10, 'profit_increase_pct')
            bars = ax6.barh(top_products['product_name'], 
                           top_products['profit_increase_pct'], 
                           color='skyblue')
            ax6.set_title('Top 10 Products - Profit Increase Potential')
            ax6.set_xlabel('Profit Increase (%)')
            
            # Add values on bars
            for bar in bars:
                width = bar.get_width()
                ax6.text(width, bar.get_y() + bar.get_height()/2.,
                        f'{width:.1f}%', ha='left', va='center')
        
        plt.tight_layout()
        plt.show()
        
        # Generate a summary metrics dashboard
        self._create_metrics_summary()
    
    def _create_metrics_summary(self):
        """Create a summary of key sales metrics"""
        plt.figure(figsize=(12, 8))
        
        # Calculate key metrics
        total_leads = len(self.lead_data)
        hot_leads = len(self.lead_data[self.lead_data['lead_priority'] == 'Very Hot'])
        conversion_rate = (self.lead_data['converted'].mean() * 100)
        
        total_customers = len(self.customer_data)
        at_risk_customers = len(self.customer_data[self.customer_data['churn_probability'] > 0.7])
        avg_clv = self.customer_data['predicted_clv'].mean()
        
        current_revenue = self.sales_data['sales'].iloc[-1] if hasattr(self, 'sales_data') else 0
        
        # Create metrics cards
        metrics = [
            ('Total Leads', f"{total_leads:,}", 'skyblue'),
            ('Hot Leads', f"{hot_leads:,}", 'lightcoral'),
            ('Conversion Rate', f"{conversion_rate:.1f}%", 'lightgreen'),
            ('Total Customers', f"{total_customers:,}", 'skyblue'),
            ('At-Risk Customers', f"{at_risk_customers:,}", 'lightcoral'),
            ('Avg. CLV', f"${avg_clv:,.0f}", 'lightgreen'),
            ('Current Monthly Revenue', f"${current_revenue:,.0f}", 'gold'),
        ]
        
        for i, (title, value, color) in enumerate(metrics):
            ax = plt.subplot(2, 4, i+1)
            ax.text(0.5, 0.7, value, ha='center', va='center', 
                   fontsize=20, weight='bold')
            ax.text(0.5, 0.3, title, ha='center', va='center', 
                   fontsize=12)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_facecolor(color)
            ax.set_xticks([])
            ax.set_yticks([])
        
        plt.suptitle('Sales Performance Metrics', fontsize=16, weight='bold')
        plt.tight_layout()
        plt.show()


def main():
    """Main function to demonstrate AI Sales capabilities"""
    print("="*50)
    print("AI FOR SALES ASSISTANT - COMPREHENSIVE DEMO")
    print("="*50)
    
    # Initialize the sales AI system
    sales_ai = AISalesAssistant()
    
    # 1. Lead Scoring
    lead_model, lead_importance = sales_ai.build_lead_scoring_model()
    
    # 2. Sales Forecasting
    forecast_model, forecast_data = sales_ai.build_sales_forecast()
    
    # 3. Pricing Optimization
    pricing_results = sales_ai.optimize_pricing()
    
    # 4. Customer Relationship Management
    crm_results = sales_ai.analyze_customer_relationships()
    
    # 5. Generate comprehensive insights
    sales_ai.generate_sales_insights()
    
    print("\n" + "="*50)
    print("AI FOR SALES DEMO COMPLETED")
    print("="*50)
    
    # Additional functionality: Export results
    try:
        # Export lead scores
        sales_ai.lead_data.to_csv('lead_scores.csv', index=False)
        print("\nLead scores exported to 'lead_scores.csv'")
        
        # Export customer insights
        sales_ai.customer_data.to_csv('customer_insights.csv', index=False)
        print("Customer insights exported to 'customer_insights.csv'")
        
        # Export pricing recommendations
        sales_ai.product_data.to_csv('pricing_recommendations.csv', index=False)
        print("Pricing recommendations exported to 'pricing_recommendations.csv'")
        
        # Export forecast
        forecast_data.to_csv('sales_forecast.csv', index=False)
        print("Sales forecast exported to 'sales_forecast.csv'")
        
    except Exception as e:
        print(f"Error exporting data: {e}")
    
    print("\nAll analysis complete. Review the generated visualizations and exported files for detailed insights.")


if __name__ == "__main__":
    main()

'''
This completes the AI Sales Assistant program with all four key components:

1. **Lead Scoring**: Uses machine learning to score and prioritize leads based on conversion probability
2. **Sales Forecasting**: Predicts future sales using time series analysis
3. **Pricing Optimization**: Optimizes product pricing to maximize profit
4. **Customer Relationship Management**: Segments customers, predicts churn, calculates CLV, and recommends actions

The program generates comprehensive visualizations and exports results to CSV files for further analysis and integration with other systems.'''

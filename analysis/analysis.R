# ==============================================================================
# Econometric Analysis in R: Modal Shift and Carbon Taxation
# Replication script using fixest (fast clustered regression) and stats
# ==============================================================================

# Required libraries
# install.packages(c("fixest", "data.table", "ggplot2", "car", "sandwich"))
library(fixest)
library(ggplot2)

data_path <- file.path("data", "processed", "analysis_long.csv")
if (!file.exists(data_path)) {
  stop("Processed data not found at: ", data_path)
}

df <- read.csv(data_path)
cat(sprintf("Loaded dataset with %d rows and %d columns.\n", nrow(df), ncol(df)))

# 1. Main Linear Probability Model with participant-clustered standard errors
lpm_mod <- feols(
  choice_car ~ treat_B + treat_C + distance_km + cost_diff + time_diff,
  cluster = ~participant_code,
  data = df
)
print(summary(lpm_mod))

# 2. Key Hypothesis Test: Wald Test of Equivalence H0: treat_B = treat_C
wald_test <- wald(lpm_mod, "treat_B = treat_C")
cat("\nWald Test of H0: treat_B = treat_C (Loss Framing == Gain Framing):\n")
print(wald_test)

# 3. Model with Demographic & Trait Controls
lpm_controls <- feols(
  choice_car ~ treat_B + treat_C + distance_km + cost_diff + time_diff +
               age + owns_car + nep_score + patience_index + risk_general,
  cluster = ~participant_code,
  data = df
)
print(summary(lpm_controls))

# 4. Heterogeneity & Interaction Effects
hetero_mod <- feols(
  choice_car ~ treat_B + treat_C +
               treat_B:owns_car + treat_C:owns_car +
               treat_B:nep_centered + treat_C:nep_centered +
               distance_km + cost_diff + owns_car + nep_score,
  cluster = ~participant_code,
  data = df
)
cat("\nHeterogeneity Estimation:\n")
print(summary(hetero_mod))

# 5. Publication-grade plot of treatment choice shares
summary_dt <- aggregate(choice_car ~ treatment, data = df, FUN = function(x) c(mean = mean(x), se = sd(x)/sqrt(length(x))))
summary_df <- data.frame(
  treatment = summary_dt$treatment,
  car_share = summary_dt$choice_car[, "mean"] * 100,
  se = summary_dt$choice_car[, "se"] * 100
)

p <- ggplot(summary_df, aes(x = treatment, y = car_share, fill = treatment)) +
  geom_bar(stat = "identity", width = 0.55, alpha = 0.85, color = "black") +
  geom_errorbar(aes(ymin = car_share - 1.96 * se, ymax = car_share + 1.96 * se), width = 0.2, linewidth = 0.8) +
  scale_fill_manual(values = c("A" = "#1e40af", "B" = "#dc2626", "C" = "#059669")) +
  scale_x_discrete(labels = c("A" = "Control (A)", "B" = "Loss: Tax (B)", "C" = "Gain: Bonus (C)")) +
  labs(
    title = "Private Car Choice Share across Policy Treatments (R Replication)",
    x = "Experimental Treatment Condition",
    y = "Private Car Share (%)"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none")

ggsave("outputs/both/r_replication_shares.png", plot = p, width = 7, height = 5, dpi = 300)
cat("\nR replication finished. Plot saved to outputs/both/r_replication_shares.png\n")
